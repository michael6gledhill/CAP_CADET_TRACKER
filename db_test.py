import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_2.0',
}


def main():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print('Connected to MySQL server version:', conn.get_server_info())
        cur = conn.cursor()
        cur.execute('SELECT idflight, flight_name FROM flight')
        flights = cur.fetchall()
        print('Flights:')
        for f in flights:
            print('  ', f)

        cur.execute('SELECT idline_position, position_name FROM line_position')
        line_positions = cur.fetchall()
        print('Line positions:')
        for lp in line_positions:
            print('  ', lp)

        conn.close()
    except Error as e:
        print('Database error:', e)


if __name__ == '__main__':
    main()
