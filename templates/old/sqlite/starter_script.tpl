"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : {{ instance_name }}
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Database connection script for {{ db_type }} instance: {{ instance_name }}
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Any, Optional, List
import os
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
def get_database_connector() -> basefunctions.DatabaseConnector:
   """
   Get a configured database connector for {{ instance_name }}.
   
   Returns
   -------
   basefunctions.DatabaseConnector
       Configured {{ db_type }} connector instance
   """
   # Create BaseDatabaseHandler instance
   db_handler = basefunctions.BaseDatabaseHandler()
   
   # Connect to database instance (configuration must exist in ConfigHandler)
   connector = db_handler.connect_to_database("{{ instance_name }}")
   
   return connector


# Example usage
if __name__ == "__main__":
   # Get the database connector
   connector: basefunctions.DatabaseConnector = get_database_connector()
   
   # Test the connection
   if connector.is_connected():
       print(f"Successfully connected to {{ db_type }} database: {{ instance_name }}")
       
       # Example queries
       try:
           # For SQLite, you can test with version query
           result: Optional[Dict[str, Any]] = connector.fetch_one("SELECT sqlite_version();")
           print(f"SQLite version: {result}")
           
           # Show all tables in database
           tables: List[Dict[str, Any]] = connector.fetch_all(
               "SELECT name FROM sqlite_master WHERE type='table';"
           )
           if tables:
               print("Tables in database:")
               for table in tables:
                   print(f"  - {table['name']}")
           else:
               print("No tables found in database")
               
       except Exception as e:
           print(f"Error executing test query: {e}")
       
       # Close connection
       connector.close()
   else:
       print("Failed to connect to database")