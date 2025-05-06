"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : backtraderfunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Extended DatabaseHandler with DataFrame caching functionality

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Optional, Any, List, Dict, Tuple
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
    extended database handler with dataframe caching capabilities
    """

    def __init__(self):
        super().__init__()
        self.dataframe_cache: Dict[Tuple[str, str], List[pd.DataFrame]] = {}
        self.logger = basefunctions.get_logger(__name__)

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

        # flush each matching cache entry
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
