-- SQL скрипт для проверки связанных данных в HubSpot CRM
-- Показывает количество связанных записей для каждой компании

-- 1. Общая сводка по компаниям и их связанным данным
SELECT 
    c.company_domain,
    c.name as company_name,
    c.industry,
    c.number_of_employees,
    COUNT(DISTINCT cca.contact_email) as total_contacts,
    COUNT(DISTINCT dca.deal_id) as total_deals,
    COUNT(DISTINCT t.ticket_id) as total_tickets,
    COUNT(DISTINCT n.note_id) as total_notes,
    COUNT(DISTINCT e.email_id) as total_emails,
    COUNT(DISTINCT ts.task_id) as total_tasks
FROM companies c
LEFT JOIN company_contact_associations cca ON c.company_domain = cca.company_domain
LEFT JOIN deal_company_associations dca ON c.company_domain = dca.company_domain
LEFT JOIN tickets t ON c.company_domain = t.company_domain
LEFT JOIN notes n ON c.company_domain = n.company_domain
LEFT JOIN contacts cont ON cca.contact_email = cont.contact_email
LEFT JOIN emails e ON cont.contact_email = e.contact_email
LEFT JOIN deals d ON dca.deal_id = d.deal_id
LEFT JOIN tasks ts ON d.deal_id = ts.deal_id
GROUP BY c.company_domain, c.name, c.industry, c.number_of_employees
ORDER BY total_contacts DESC, total_deals DESC;

-- 2. Детальная информация по конкретной компании (замените 'oliver.com' на нужную)
-- SELECT '=== COMPANY DETAILS ===' as info;
-- SELECT company_domain, name, industry, number_of_employees 
-- FROM companies 
-- WHERE company_domain = 'oliver.com';

-- SELECT '=== CONTACTS ===' as info;
-- SELECT contact_email, first_name, last_name, mobile_phone
-- FROM contacts 
-- WHERE company_domain = 'oliver.com'
-- LIMIT 5;

-- SELECT '=== DEALS ===' as info;
-- SELECT deal_id, deal_name, deal_stage, amount, close_date
-- FROM deals 
-- WHERE company_domain = 'oliver.com'
-- LIMIT 5;

-- SELECT '=== TICKETS ===' as info;
-- SELECT ticket_id, LEFT(ticket_name, 50) || '...' as ticket_name_short, 
--        ticket_status, priority, issue_of_interest
-- FROM tickets 
-- WHERE company_domain = 'oliver.com'
-- LIMIT 5;

-- 3. Проверка целостности связей
-- SELECT '=== RELATIONSHIP INTEGRITY ===' as info;
-- SELECT 
--     'orphaned_contacts' as issue_type,
--     COUNT(*) as count
-- FROM contacts c
-- LEFT JOIN company_contact_associations cca ON c.contact_email = cca.contact_email
-- WHERE cca.contact_email IS NULL
-- 
-- UNION ALL
-- 
-- SELECT 
--     'orphaned_deals' as issue_type,
--     COUNT(*) as count
-- FROM deals d
-- LEFT JOIN deal_company_associations dca ON d.deal_id = dca.deal_id
-- WHERE dca.deal_id IS NULL; 