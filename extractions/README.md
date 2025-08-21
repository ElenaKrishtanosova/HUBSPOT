# Data Export Scripts for HubSpot

This directory contains scripts for exporting database data to CSV format, with special support for HubSpot CSV imports.

## 📁 Files

### `extractions.py`
- **Purpose**: General database export to CSV
- **Features**: 
  - Exports all database tables
  - Converts TIMESTAMPTZ dates to readable format
  - Creates sample data files
  - Basic CSV formatting

### `hubspot_export.py`
- **Purpose**: HubSpot-specific CSV export
- **Features**:
  - Maps database fields to HubSpot field names
  - Formats dates according to HubSpot requirements
  - Creates files ready for HubSpot import
  - Optimized for HubSpot CSV import process

## 🚀 Usage

### Basic Export (all tables)
```bash
cd extractions
python extractions.py
```

### HubSpot-Specific Export
```bash
cd extractions
python hubspot_export.py
```

## 📊 HubSpot Field Mappings

### Deals
| Database Field | HubSpot Field | Date Format |
|----------------|----------------|-------------|
| `deal_id` | Deal ID | - |
| `deal_name` | Deal Name | - |
| `deal_stage` | Deal Stage | - |
| `description` | Description | - |
| `contact_email` | Associated Contact Email | - |
| `company_domain` | Associated Company Domain | - |
| `activity_date` | Close Date | M/D/YYYY |

### Tasks
| Database Field | HubSpot Field | Date Format |
|----------------|----------------|-------------|
| `task_id` | Task ID | - |
| `title` | Subject | - |
| `notes` | Description | - |
| `assigned_to_user_id` | Assigned To | - |
| `deal_id` | Associated Deal ID | - |
| `created_at` | Due Date | M/D/YY HH:MM |

### Tickets
| Database Field | HubSpot Field | Date Format |
|----------------|----------------|-------------|
| `ticket_id` | Ticket ID | - |
| `ticket_name` | Subject | - |
| `priority` | Priority | - |
| `issue_of_interest` | Issue Type | - |
| `description` | Description | - |
| `contact_email` | Contact Email | - |
| `company_domain` | Company Domain | - |
| `ticket_owner` | Owner | - |
| `activity_date` | Created Date | M/D/YYYY HH:MM |

## 📅 Date Format Conversion

The scripts automatically convert TIMESTAMPTZ database dates to HubSpot-compatible formats:

- **Deals**: `3/16/2018` (M/D/YYYY)
- **Tasks**: `3/16/18 14:30` (M/D/YY HH:MM)
- **Tickets**: `3/16/2018 14:30` (M/D/YYYY HH:MM)
- **Notes**: `3/16/2018` (M/D/YYYY)
- **Calls**: `3/16/2018 14:30` (M/D/YYYY HH:MM)
- **Emails**: `3/16/2018 14:30` (M/D/YYYY HH:MM)

## 🔧 Configuration

Both scripts use the same configuration from `../config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  user: postgres
  password: your_password
  name: hubspot_crm

logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

## 📋 Output Files

### Standard Export (`extractions.py`)
- `companies.csv`
- `contacts.csv`
- `deals.csv`
- `tickets.csv`
- `tasks.csv`
- `calls.csv`
- `emails.csv`
- `notes.csv`

### HubSpot Export (`hubspot_export.py`)
- `HubSpot_Deals.csv`
- `HubSpot_Contacts.csv`
- `HubSpot_Companies.csv`
- `HubSpot_Tickets.csv`
- `HubSpot_Tasks.csv`

## ⚠️ Important Notes

1. **Date Formats**: All dates are automatically converted to HubSpot-compatible formats
2. **Field Mapping**: HubSpot export uses predefined field mappings
3. **Sample Data**: Scripts create sample files if no database connection is available
4. **Encoding**: All CSV files use UTF-8 encoding
5. **Headers**: HubSpot export includes proper field headers for import

## 🎯 Use Cases

- **Data Migration**: Move data from local database to HubSpot
- **Backup**: Create CSV backups of database tables
- **Integration**: Prepare data for other CRM systems
- **Analysis**: Export data for external analysis tools
- **Testing**: Create sample data for development/testing

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `config.yaml` settings
   - Verify database is running
   - Check environment variables

2. **Date Format Errors**
   - Ensure database has TIMESTAMPTZ fields
   - Run `update_date_formats.py` if needed

3. **Permission Denied**
   - Check write permissions in output directory
   - Ensure script has database access

### Error Messages

- `Configuration file not found`: Check `config.yaml` path
- `Error getting table names`: Database connection issue
- `No HubSpot mapping found`: Entity type not supported 