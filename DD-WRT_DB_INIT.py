import sqlite3
import os

def main():

    database_name = 'DDWRT_MONITOR'
    script_path = os.path.dirname(__file__)


    DDWRT_MONITOR_TABLE ='''
    CREATE TABLE DDWRT_MONITOR (
        ROWID INTEGER PRIMARY KEY AUTOINCREMENT ,
        current_time TEXT,
        mem_total INTEGER,
        mem_free INTEGER,
        system_load_1min REAL,
        system_load_5min REAL,
        system_load_15min REAL,
        active_connections INTEGER,
        cpu_temp REAL,
        nvram_used INTEGER,
        nvram_total INTEGER,
        traffic_in INTEGER,
        traffic_out INTEGER,
        uptime INTEGER,
        external_packet_loss REAL,
        external_ping_roundtrip_min REAL,
        external_ping_roundtrip_avg REAL,
        external_ping_roundtrip_max REAL,
        internal_packet_loss REAL,
        internal_ping_roundtrip_min REAL,
        internal_ping_roundtrip_avg REAL,
        internal_ping_roundtrip_max REAL
        )
    '''

    try:
        connection = sqlite3.connect(os.path.join(script_path, database_name))

        cursor = connection.cursor()

        cursor.execute(DDWRT_MONITOR_TABLE)

        connection.commit()

        connection.close()

    except Exception as e:
        print(e)




if __name__ == '__main__':
    main()
