-- =============================================================================
-- RAG Sales Chatbot — Seed Data
-- Sample modules and pricing rules for development/testing
-- =============================================================================

-- =============================================================================
-- Modules
-- =============================================================================
INSERT INTO modules (id, name, description, features, category) VALUES

('starter', 'Starter Plan',
 'Perfect for individuals and freelancers who need basic tools to manage their work. Includes essential project management, time tracking, and invoicing capabilities.',
 '["Project management (up to 5 projects)", "Time tracking", "Basic invoicing", "Email support", "1 GB storage"]'::jsonb,
 'plan'),

('professional', 'Professional Plan',
 'Designed for small to medium businesses that need a complete suite of tools. Includes everything in Starter plus HR management, payroll processing, advanced reporting, and CRM capabilities.',
 '["Unlimited projects", "Advanced time tracking & reporting", "Full invoicing & billing", "HR management", "Payroll processing", "Basic CRM", "Priority email & chat support", "10 GB storage", "Team collaboration tools", "API access"]'::jsonb,
 'plan'),

('enterprise', 'Enterprise Plan',
 'Built for large organizations requiring maximum control, security, and customization. Includes everything in Professional plus dedicated account management, custom integrations, SSO, audit logs, and unlimited storage.',
 '["Everything in Professional", "Single Sign-On (SSO)", "Audit logs & compliance reporting", "Custom integrations", "Dedicated account manager", "24/7 phone support", "Unlimited storage", "Advanced security controls", "Custom workflows", "SLA guarantee (99.9% uptime)"]'::jsonb,
 'plan'),

('crm_addon', 'CRM Add-on',
 'Advanced Customer Relationship Management module. Track leads, manage sales pipelines, automate follow-ups, and generate sales reports. Works with Professional and Enterprise plans.',
 '["Lead tracking & scoring", "Sales pipeline management", "Automated follow-up emails", "Contact management", "Sales analytics & reports", "Integration with email providers"]'::jsonb,
 'addon'),

('analytics_addon', 'Analytics Add-on',
 'Business intelligence and advanced analytics module. Create custom dashboards, generate detailed reports, and gain insights from your data. Works with all plans.',
 '["Custom dashboards", "Advanced reporting engine", "Data export (CSV, PDF, Excel)", "Scheduled reports", "Real-time metrics", "Cross-module analytics"]'::jsonb,
 'addon'),

('payroll_addon', 'Payroll Add-on',
 'Comprehensive payroll processing module for businesses of any size. Handles tax calculations, direct deposits, pay stubs, and compliance. Available as add-on for Starter plan users.',
 '["Automated payroll calculation", "Tax filing & compliance", "Direct deposit", "Pay stub generation", "Multi-state payroll", "Year-end tax forms (W-2, 1099)"]'::jsonb,
 'addon'),

('storage_addon', 'Extra Storage Add-on',
 'Additional cloud storage for documents, files, and backups. Available in 50 GB increments.',
 '["50 GB additional storage per unit", "Automatic backups", "File versioning", "Secure file sharing"]'::jsonb,
 'addon')

ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  features = EXCLUDED.features,
  category = EXCLUDED.category,
  updated_at = NOW();

-- =============================================================================
-- Pricing Rules
-- =============================================================================

-- Starter Plan pricing
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('starter', 'individual', 1, 1, 9.99, 0.00, 'USD', 'monthly'),
('starter', 'small_team', 2, 10, 8.99, 0.00, 'USD', 'monthly'),
('starter', 'team', 11, 50, 7.99, 0.00, 'USD', 'monthly')
ON CONFLICT DO NOTHING;

-- Professional Plan pricing
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('professional', 'small_team', 1, 10, 24.99, 0.00, 'USD', 'monthly'),
('professional', 'medium', 11, 50, 21.99, 0.00, 'USD', 'monthly'),
('professional', 'large', 51, 200, 18.99, 0.00, 'USD', 'monthly')
ON CONFLICT DO NOTHING;

-- Enterprise Plan pricing
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('enterprise', 'standard', 1, 100, 49.99, 500.00, 'USD', 'monthly'),
('enterprise', 'large', 101, 500, 44.99, 500.00, 'USD', 'monthly'),
('enterprise', 'unlimited', 501, NULL, 39.99, 1000.00, 'USD', 'monthly')
ON CONFLICT DO NOTHING;

-- CRM Add-on pricing
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('crm_addon', 'standard', 1, 50, 7.99, 0.00, 'USD', 'monthly'),
('crm_addon', 'large', 51, NULL, 5.99, 0.00, 'USD', 'monthly')
ON CONFLICT DO NOTHING;

-- Analytics Add-on pricing
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('analytics_addon', 'standard', 1, 50, 4.99, 0.00, 'USD', 'monthly'),
('analytics_addon', 'large', 51, NULL, 3.99, 0.00, 'USD', 'monthly')
ON CONFLICT DO NOTHING;

-- Payroll Add-on pricing
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('payroll_addon', 'standard', 1, 50, 6.99, 0.00, 'USD', 'monthly'),
('payroll_addon', 'large', 51, NULL, 5.49, 0.00, 'USD', 'monthly')
ON CONFLICT DO NOTHING;

-- Extra Storage Add-on pricing (flat fee per 50 GB block, not per user)
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee, currency, billing_cycle) VALUES
('storage_addon', 'standard', 1, NULL, 0.00, 9.99, 'USD', 'monthly')
ON CONFLICT DO NOTHING;
