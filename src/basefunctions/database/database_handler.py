"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

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


class DatabaseHandler(basefunctions.BaseDatabaseHandler):
    """
    enhanced database handler with optional dataframe caching and threadpool support
    """

    def __init__(
        self, cached: bool = False, use_threadpool: bool = False, max_cache_size: int = 10
    ):
        """
        initialize database handler

        parameters
        ----------
        cached : bool
            whether to cache dataframes before writing to database
        use_threadpool : bool
            whether to use threadpool for database operations
        max_cache_size : int
            maximum number of dataframes in cache before auto-flushing
        """
        super().__init__()
        self.cached = cached
        self.use_threadpool = use_threadpool
        self.max_cache_size = max_cache_size
        self.dataframe_cache: Dict[Tuple[str, str], List[pd.DataFrame]] = {}
        self.logger = basefunctions.get_logger(__name__)
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
                    instance_name = content.get("instance_name")
                    table = content.get("table_name")
                    df = content.get("dataframe")
                    db_type = content.get("db_type")
                    connection_params = content.get("connection_params")

                    # Store connectors in thread local data
                    if not hasattr(context.thread_local_data, "db_connectors"):
                        context.thread_local_data.db_connectors = {}

                    # Create or reuse connector
                    if instance_name not in context.thread_local_data.db_connectors:
                        # Create connector based on provided db_type
                        connector_map = {
                            "sqlite3": basefunctions.SQLiteConnector,
                            "mysql": basefunctions.MySQLConnector,
                            "postgresql": basefunctions.PostgreSQLConnector,
                        }

                        if db_type not in connector_map:
                            raise ValueError(f"unsupported db_type '{db_type}'")

                        connector_class = connector_map[db_type]
                        connector = connector_class(connection_params)
                        context.thread_local_data.db_connectors[instance_name] = connector

                    connector = context.thread_local_data.db_connectors[instance_name]

                    # Use the connector with transaction
                    with connector.transaction():
                        connection = connector.get_connection()
                        df.to_sql(table, connection, if_exists="append", index=False)

                    return True, {"rows": len(df), "instance": instance_name, "table": table}
                except Exception as e:
                    return False, str(e)

        return FlushDataframeHandler

    def add_dataframe(self, instance_name: str, table_name: str, df: pd.DataFrame) -> None:
        """
        add dataframe to database - either directly or to cache for later processing

        parameters
        ----------
        instance_name : str
            instance name identifier
        table_name : str
            target table name
        df : pd.DataFrame
            dataframe to be written
        """
        if not self.cached:
            # Direct write mode
            if self.use_threadpool:
                self._write_dataframe_direct_with_threadpool(instance_name, table_name, df)
            else:
                self._write_dataframe_direct_without_threadpool(instance_name, table_name, df)
        else:
            # Cached mode
            cache_key = (instance_name, table_name)
            if cache_key not in self.dataframe_cache:
                self.dataframe_cache[cache_key] = []

            self.dataframe_cache[cache_key].append(df)

            # Check if auto-flush is needed
            if self._check_cache_size(cache_key):
                self.flush(instance_name, table_name)

    def _write_dataframe_direct_with_threadpool(
        self, instance_name: str, table_name: str, df: pd.DataFrame
    ) -> str:
        """
        write dataframe directly to database using threadpool

        parameters
        ----------
        instance_name : str
            instance name identifier
        table_name : str
            target table name
        df : pd.DataFrame
            dataframe to be written

        returns
        -------
        str
            task id from the threadpool
        """
        if not self.threadpool:
            self._init_threadpool()

        if not self.threadpool:
            self.logger.warning("threadpool initialization failed, falling back to direct write")
            return self._write_dataframe_direct_without_threadpool(instance_name, table_name, df)

        task_id = self.threadpool.submit_task(
            message_type="flush_dataframe",
            content={"instance_name": instance_name, "table_name": table_name, "dataframe": df},
        )
        return task_id

    def _write_dataframe_direct_without_threadpool(
        self, instance_name: str, table_name: str, df: pd.DataFrame
    ) -> None:
        """
        write dataframe directly to database without using threadpool

        parameters
        ----------
        instance_name : str
            instance name identifier
        table_name : str
            target table name
        df : pd.DataFrame
            dataframe to be written
        """
        try:
            # write to database within a transaction
            with self.transaction(instance_name):
                # use pandas to_sql for simplicity
                connection = self.get_connection(instance_name)
                df.to_sql(table_name, connection, if_exists="append", index=False)
        except Exception as e:
            self.logger.error(f"failed to write dataframe to {instance_name}.{table_name}: {e}")
            raise

    def flush(self, instance_name: Optional[str] = None, table_name: Optional[str] = None) -> None:
        """
        write all cached dataframes to database

        parameters
        ----------
        instance_name : Optional[str]
            specific instance to flush, all if None
        table_name : Optional[str]
            specific table to flush, all if None
        """
        if not self.cached:
            return

        # determine which cache entries to process
        keys_to_flush = []
        for key in list(self.dataframe_cache.keys()):
            inst_name, table = key
            if (instance_name is None or inst_name == instance_name) and (
                table_name is None or table == table_name
            ):
                keys_to_flush.append(key)

        # use threadpool if enabled
        if self.use_threadpool and self.threadpool:
            self._flush_with_threadpool(keys_to_flush)
        else:
            self._flush_without_threadpool(keys_to_flush)

    def _flush_with_threadpool(self, keys_to_flush: List[Tuple[str, str]]) -> None:
        """
        flush cached dataframes using threadpool

        parameters
        ----------
        keys_to_flush : List[Tuple[str, str]]
            list of (instance_name, table_name) keys to flush
        """
        task_ids = []

        for key in keys_to_flush:
            inst_name, table = key
            frames = self.dataframe_cache[key]

            if not frames:
                continue

            # concatenate all dataframes
            combined_df = pd.concat(frames, ignore_index=True)

            # submit task to threadpool
            task_id = self.threadpool.submit_task(
                message_type="flush_dataframe",
                content={
                    "instance_name": inst_name,
                    "table_name": table,
                    "dataframe": combined_df,
                },
            )
            task_ids.append((task_id, key))

            # clear the cache after submission
            del self.dataframe_cache[key]

    def _flush_without_threadpool(self, keys_to_flush: List[Tuple[str, str]]) -> None:
        """
        flush cached dataframes without using threadpool

        parameters
        ----------
        keys_to_flush : List[Tuple[str, str]]
            list of (instance_name, table_name) keys to flush
        """
        for key in keys_to_flush:
            inst_name, table = key
            frames = self.dataframe_cache[key]

            if not frames:
                continue

            # concatenate all dataframes
            combined_df = pd.concat(frames, ignore_index=True)

            try:
                # write to database within a transaction
                with self.transaction(inst_name):
                    # use pandas to_sql for simplicity
                    connection = self.get_connection(inst_name)
                    combined_df.to_sql(table, connection, if_exists="append", index=False)

                # clear the cache after successful write
                del self.dataframe_cache[key]
            except Exception as e:
                self.logger.error(f"failed to flush dataframe to {inst_name}.{table}: {e}")
                # Keep the dataframe in cache for potential retry
                raise

    def clear_cache(
        self, instance_name: Optional[str] = None, table_name: Optional[str] = None
    ) -> None:
        """
        clear dataframe cache without writing to database

        parameters
        ----------
        instance_name : Optional[str]
            specific instance to clear, all if None
        table_name : Optional[str]
            specific table to clear, all if None
        """
        if not self.cached:
            return

        keys_to_clear = []
        for key in self.dataframe_cache.keys():
            inst_name, table = key
            if (instance_name is None or inst_name == instance_name) and (
                table_name is None or table == table_name
            ):
                keys_to_clear.append(key)

        for key in keys_to_clear:
            del self.dataframe_cache[key]

    def get_cache_info(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        get information about cached dataframes

        returns
        -------
        Dict[Tuple[str, str], Dict[str, Any]]
            mapping of (instance_name, table_name) to cache statistics
        """
        if not self.cached:
            return {}

        result = {}
        for key, frames in self.dataframe_cache.items():
            df_count = len(frames)
            row_count = sum(len(df) for df in frames)
            result[key] = {"dataframes": df_count, "total_rows": row_count}
        return result

    def _check_cache_size(self, key: Tuple[str, str]) -> bool:
        """
        check if cache size for a specific key exceeds max_cache_size

        parameters
        ----------
        key : Tuple[str, str]
            (instance_name, table_name) key to check

        returns
        -------
        bool
            true if cache exceeds the maximum number of dataframes allowed
        """
        if key not in self.dataframe_cache:
            return False

        return len(self.dataframe_cache[key]) >= self.max_cache_size

    def get_database_connector(
        self, instance_name: str, connect: bool = True
    ) -> "basefunctions.DatabaseConnector":
        """
        Create and return a database connector for the specified instance.

        Parameters
        ----------
        instance_name : str
            Name of the database instance (e.g., 'dev_asset_db_postgres')
        connect : bool, optional
            Whether to automatically establish connection, by default True

        Returns
        -------
        basefunctions.DatabaseConnector
            Configured database connector instance

        Raises
        ------
        ValueError
            If instance is not found or has invalid configuration
        RuntimeError
            If connector creation fails
        """
        # Use the parent's connect_to_database method
        return self.connect_to_database(instance_name, connect)
