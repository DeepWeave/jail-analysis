// Update with your config settings.

const user = process.env.JDB_USER
const password = process.env.JDB_PASSWORD
const host = process.env.JDB_HOST
const database = process.env.JDB_NAME
const min = parseInt(process.env.JDB_POOL_MIN, 10)
const max = parseInt(process.env.JDB_POOL_MAX, 10)
const tableName = process.env.DB_MIGRATIONS_TABLE

const connection = {
  host,
  database,
  user,
  password
}

if (process.env.DB_HOST !== 'localhost') {
  connection['ssl'] =   { rejectUnauthorized: false };
}

module.exports = {
  client: 'postgresql',
  connection,
  pool: {
    min,
    max
  },
  migrations: {
    tableName
  }
};
