import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv


class Record:
    def __init__(self):
        """
        we gonna create the engine object for init
        """
        self.engine = self.create_engine()

    def create_engine(self):
        load_dotenv()
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_sslmode = os.getenv('DB_SSLMODE')

        # create the engine
        engine = create_engine(
            f"postgresql://{db_user}:{db_password}@"
            f"{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}")
        return engine

    def add_record(self, record: dict) -> None:
        """
        this function add a record into the postgres (aiven) db
        :param record: a dictionary with the info to be added
        :return: None
        """

        # add table
        table_name = 'operations'

        # create record
        df = pd.DataFrame(record)
        msg = f"the new record, now is df, the value is {df}"
        print(msg)
        # add record
        df.to_sql(table_name, self.engine, if_exists='append', index=False)

        print("Data inserted successfully!")

        """
            the record must be passed as pd
            Example for add a record
            strategy: name of strategy
            ticker: pair traded
            side: buy or sell
            quantity: qty of pair
            price: average price
            type: there's origin, sl, exit_sl, direct_tp, indirect_tp, end
            fee: binance's futures fee
            binance_operation_id: number of id of the operation in binance
            operation_id: intern operation_id
            epoch: binance epoch of the operation
            pnl: raw profit
            """
        return

    def read_record(self, operation_id):
        table_name = 'operations'  # Replace with your actual table name

        try:
            with self.engine.connect() as connection:
                query = (f"SELECT * FROM {table_name} WHERE"
                         f" operation_id={operation_id};")
                df = pd.read_sql(query, connection)
            print(f"Data for operation_id {operation_id}"
                  f" is ready")
            return df.to_dict(orient='records')
        except Exception as e:
            print(f"Error reading data: {e}")
            return None

    def read_db(self):
        table_name = 'operations'  # Replace with your actual table name

        try:
            with self.engine.connect() as connection:
                query = f"SELECT * FROM {table_name};"
                df = pd.read_sql(query, connection)
            print(f"Data for db is ready")
            return df.to_dict(orient='records')
        except Exception as e:
            print(f"Error reading data: {e}")
            return None

    def edit_record(self, operation_id, changes):
        """
            changes is a key/value pair as
                {
                    'column': 'column_to_update',
                    'new_value': 'new_value'
                }
        """
        table_name = 'operations'

        # in order to avoid sql injection code, let's acotate
        allowed_columns = ['side', 'price', 'type', 'commission', 'fee',
                           'epoch'
                           ]

        column = changes.get('column')
        new_value = changes.get('new_value')

        if column not in allowed_columns:
            print(f"Error: Column '{column}' is not allowed for editing.")
            return

        if 'column' and 'new_value' in changes:
            try:
                with self.engine.connect() as connection:
                    raw_sql = f"""
                        UPDATE {table_name}
                        SET "{column}" = :new_value
                        WHERE operation_id = :sql_operation_id
                    """
                    query = text(raw_sql)
                    connection.execute(query,
                                       {
                                           'new_value': new_value,
                                           'sql_operation_id': operation_id
                                       }
                                       )  # Pass parameters directly as a dictionary
                    connection.commit()
                    print(f"Operation with Id {operation_id} "
                          f"updated successfully.")
            except Exception as e:
                print(f"Error updating data: {e}")
        else:
            print(
                "Error: 'column' and 'new_value' "
                "keys are required in the changes dictionary.")

    def delete_record(self, operation_id):
        table_name = 'operations'
        try:
            with self.engine.connect() as connection:
                raw_sql = f"""
                    DELETE FROM {table_name}
                    WHERE operation_id = :id_to_delete
                """
                query = text(raw_sql)
                connection.execute(query,
                                   {
                                       'id_to_delete': operation_id
                                   }
                                   )
                connection.commit()  # Important to commit changes
                print(f"the record {operation_id} was deleted successfully.")
        except Exception as e:
            print(f"Error deleting data: {e}")

    def get_max_id(self):
        """this function returns the max id in operations table"""
        table_name = 'operations'
        try:
            with self.engine.connect() as connection:
                query = (f"SELECT MAX(operation_id) AS max_id "
                         f"FROM {table_name};"
                         )
                df = pd.read_sql(query, connection)
                return df
        except Exception as e:
            print(f"Error deleting data: {e}")
            return None
