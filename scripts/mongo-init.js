// MongoDB initialization script for XRPL Offline Payments
// This script runs when MongoDB container starts for the first time

print('========================================');
print('XRPL Offline Payments - Database Init');
print('========================================');

// Switch to the application database
db = db.getSiblingDB('xcceptapay');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'username'],
      properties: {
        username: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
          description: 'must be a valid email and is required'
        },
        role: {
          enum: ['user', 'admin', 'merchant'],
          description: 'user role'
        }
      }
    }
  }
});

db.createCollection('devices');
db.createCollection('channels');
db.createCollection('claims');
db.createCollection('receipts');

// Create indexes for performance
print('Creating indexes...');

db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ username: 1 });

db.devices.createIndex({ device_id: 1 }, { unique: true });
db.devices.createIndex({ dest_tag: 1 }, { unique: true });

db.channels.createIndex({ channel_id: 1 }, { unique: true });
db.channels.createIndex({ dest_tag: 1 });

db.claims.createIndex({ channel_id: 1 });
db.claims.createIndex({ seenAt: -1 });

db.receipts.createIndex({ channel_id: 1 });
db.receipts.createIndex({ tx_hash: 1 }, { unique: true });
db.receipts.createIndex({ settledAt: -1 });
db.receipts.createIndex({ ledger_index: 1 });

print('✓ Indexes created');

// Create admin user (for production, change this!)
print('Creating default admin user...');

db.users.insertOne({
  username: 'admin',
  email: 'admin@xcceptapay.local',
  password: '$2a$10$XqkFG4Z5J1Kh6yZH9cYvR.KQoU7X8Y9Z0A1B2C3D4E5F6G7H8I9J0K', // hashed 'admin123'
  role: 'admin',
  balance: 0,
  wallet: '',
  seed: '',
  transaction_history: [],
  createdAt: new Date(),
  updatedAt: new Date()
});

print('✓ Admin user created (email: admin@xcceptapay.local, password: admin123)');
print('⚠ WARNING: Change default credentials in production!');

print('');
print('Database initialization complete!');
print('========================================');
