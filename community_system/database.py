"""Database models and initialization"""
import sqlite3
import os
from datetime import datetime

# Use /data for Render persistent storage, fallback to local
if os.path.exists('/data'):
    DATABASE = '/data/community.db'
else:
    DATABASE = 'community.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Table 1: event_types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    
    # Table 2: organizations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            size TEXT,
            contact_name TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 3: volunteers (individual donation accounts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 4: event_profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_date DATE NOT NULL,
            event_type_id INTEGER,
            location TEXT,
            description TEXT,
            organization_id INTEGER,
            coordinator_name TEXT,
            coordinator_phone TEXT,
            coordinator_email TEXT,
            expected_participants INTEGER DEFAULT 0,
            actual_participants INTEGER DEFAULT 0,
            income REAL DEFAULT 0,
            expense REAL DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT 'In Progress',
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            quarter TEXT,
            FOREIGN KEY (event_type_id) REFERENCES event_types(id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
    ''')
    
    # Table 5: contributions (with volunteer_id link)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            volunteer_id INTEGER,
            volunteer_name TEXT NOT NULL,
            volunteer_contact TEXT,
            volunteer_hours REAL DEFAULT 0,
            cash_donation REAL DEFAULT 0,
            material_description TEXT,
            material_value REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES event_profiles(id) ON DELETE CASCADE,
            FOREIGN KEY (volunteer_id) REFERENCES volunteers(id)
        )
    ''')
    
    # Table 6: quarterly_summaries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quarterly_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            total_events INTEGER DEFAULT 0,
            total_volunteer_hours REAL DEFAULT 0,
            total_cash_donations REAL DEFAULT 0,
            total_material_value REAL DEFAULT 0,
            total_participants INTEGER DEFAULT 0,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, quarter)
        )
    ''')
    
    # Insert default event types
    default_types = [('School', 'School related activities'), ('Church', 'Church related activities'), 
                     ('Community', 'Community related activities'), ('Other', 'Other activities')]
    for name, desc in default_types:
        cursor.execute('INSERT OR IGNORE INTO event_types (name, description) VALUES (?, ?)', (name, desc))
    
    conn.commit()
    conn.close()

def calculate_quarter(date_str):
    """Calculate quarter from date"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    quarter = (date.month - 1) // 3 + 1
    return f"{date.year}Q{quarter}"

if __name__ == '__main__':
    init_db()
    print("Database initialized!")
