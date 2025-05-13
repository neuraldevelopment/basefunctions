"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Extended DatabaseHandler with DataFrame caching and ThreadPool capabilities

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict, Tuple, Type
import pandas as pd
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class CachingDatabaseHandler(basefunctions.DatabaseHandler):
    """
    extended database handler with dataframe caching capabilities and threadpool support
    """

    def __init__(self, use_threadpool: bool = False):
        super().__init__()
        self.dataframe_cache: Dict[Tuple[str, str], List[pd.DataFrame]] = {}
        self.logger = basefunctions.get_logger(__name__)
        self.use_threadpool = use_threadpool
        self.threadpool = None

        if self.use_threadpool:
            self._init_threadpool()

    def _init_threadpool(self) -> None:
        """
        initialize threadpool and register handler
        """
        try:
            # Import here to avoid circular import issues
            ThreadPool = basefunctions.ThreadPool
            self.threadpool = ThreadPool()

            # Create handler class dynamically
            handler_class = self._create_flush_handler_class()

            self.threadpool.register_handler("flush_dataframe", handler_class, "thread")
            self.logger.info("threadpool initialized for database operations")
        except Exception as e:
            self.logger.error(f"failed to initialize threadpool: {e}")
            self.use_threadpool = False

    def _create_flush_handler_class(self) -> Type:
        """
        dynamically creates a handler class for the threadpool

        returns
        -------
        Type
            a class that implements ThreadPoolRequestInterface
        """

        class FlushDataframeHandler(basefunctions.ThreadPoolRequestInterface):
            """
            thread pool handler to flush dataframe to database
            """

            def process_request(self, context, message):
                try:
                    content = message.content
                    conn_id = content.get("connector_id")
                    table = content.get("table_name")
                    df = content.get("dataframe")

                    # Use DatabaseHandler directly
                    db_handler = basefunctions.DatabaseHandler()
                    with db_handler.transaction(conn_id):
                        connection = db_handler.get_connection(conn_id)
                        df.to_sql(table, connection, if_exists="append", index=False)

                    return True, {"rows": len(df), "connector": conn_id, "table": table}
                except Exception as e:
                    return False, str(e)

        return FlushDataframeHandler

    def add_dataframe(self, connector_id: str, table_name: str, df: pd.DataFrame) -> None:
        """
        add dataframe to cache for later batch processing

        parameters
        ----------
        connector_id : str
            connector identifier
        table_name : str
            target table name
        df : pd.DataFrame
            dataframe to be cached
        """
        cache_key = (connector_id, table_name)
        if cache_key not in self.dataframe_cache:
            self.dataframe_cache[cache_key] = []

        self.dataframe_cache[cache_key].append(df)
        self.logger.debug(f"added dataframe to cache for {connector_id}.{table_name}")

    def _flush_with_threadpool(self, keys_to_flush: List[Tuple[str, str]]) -> None:
        """
        flush cached dataframes using threadpool

        parameters
        ----------
        keys_to_flush : List[Tuple[str, str]]
            list of (connector_id, table_name) keys to flush
        """
        task_ids = []

        for key in keys_to_flush:
            conn_id, table = key
            frames = self.dataframe_cache[key]

            if not frames:
                continue

            # concatenate all dataframes
            combined_df = pd.concat(frames, ignore_index=True)

            # submit task to threadpool
            task_id = self.threadpool.submit_task(
                message_type="flush_dataframe",
                content={"connector_id": conn_id, "table_name": table, "dataframe": combined_df},
            )
            task_ids.append((task_id, key))
            self.logger.debug(f"submitted flush task {task_id} for {conn_id}.{table}")

            # clear the cache after submission
            del self.dataframe_cache[key]

        # optional: could wait for results here

    def flush(self, connector_id: Optional[str] = None, table_name: Optional[str] = None) -> None:
        """
        write all cached dataframes to database

        parameters
        ----------
        connector_id : Optional[str]
            specific connector to flush, all if None
        table_name : Optional[str]
            specific table to flush, all if None
        """
        # determine which cache entries to process
        keys_to_flush = []
        for key in self.dataframe_cache.keys():
            conn_id, table = key
            if (connector_id is None or conn_id == connector_id) and (
                table_name is None or table == table_name
            ):
                keys_to_flush.append(key)

        if not keys_to_flush:
            return

        # use threadpool if enabled
        if self.use_threadpool and self.threadpool:
            self._flush_with_threadpool(keys_to_flush)
            return

        # regular flush implementation (original code)
        for key in keys_to_flush:
            conn_id, table = key
            frames = self.dataframe_cache[key]

            if not frames:
                continue

            # concatenate all dataframes
            combined_df = pd.concat(frames, ignore_index=True)

            # write to database within a transaction
            with self.transaction(conn_id):
                # use pandas to_sql for simplicity
                connection = self.get_connection(conn_id)
                combined_df.to_sql(table, connection, if_exists="append", index=False)

            # clear the cache after successful write
            del self.dataframe_cache[key]
            self.logger.info(f"flushed {len(combined_df)} rows to {conn_id}.{table}")

    def clear_cache(
        self, connector_id: Optional[str] = None, table_name: Optional[str] = None
    ) -> None:
        """
        clear dataframe cache without writing to database

        parameters
        ----------
        connector_id : Optional[str]
            specific connector to clear, all if None
        table_name : Optional[str]
            specific table to clear, all if None
        """
        keys_to_clear = []
        for key in self.dataframe_cache.keys():
            conn_id, table = key
            if (connector_id is None or conn_id == connector_id) and (
                table_name is None or table == table_name
            ):
                keys_to_clear.append(key)

        for key in keys_to_clear:
            del self.dataframe_cache[key]

        self.logger.info(f"cleared {len(keys_to_clear)} cache entries")

    def get_cache_info(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        get information about cached dataframes

        returns
        -------
        Dict[Tuple[str, str], Dict[str, Any]]
            mapping of (connector_id, table_name) to cache statistics
        """
        result = {}
        for key, frames in self.dataframe_cache.items():
            df_count = len(frames)
            row_count = sum(len(df) for df in frames)
            result[key] = {"dataframes": df_count, "total_rows": row_count}
        return result
