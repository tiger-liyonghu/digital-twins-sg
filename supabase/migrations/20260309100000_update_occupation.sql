-- Script 21: Update occupation for all employed agents using CPT
-- Run in Supabase SQL Editor (60-second timeout, not 8-second REST limit)
-- Set seed for reproducibility
SELECT setseed(0.42);

WITH cpt AS (
  SELECT * FROM (VALUES
    ('University',     'young',  0.10, 0.50, 0.32, 0.04, 0.02, 0.005, 0.003, 0.001, 0.001),
    ('University',     'mid',    0.25, 0.40, 0.27, 0.04, 0.02, 0.008, 0.005, 0.004, 0.003),
    ('University',     'senior', 0.30, 0.35, 0.26, 0.04, 0.03, 0.008, 0.005, 0.004, 0.003),
    ('Postgraduate',   'young',  0.12, 0.52, 0.30, 0.03, 0.02, 0.003, 0.003, 0.001, 0.003),
    ('Postgraduate',   'mid',    0.26, 0.42, 0.26, 0.03, 0.02, 0.005, 0.003, 0.003, 0.002),
    ('Postgraduate',   'senior', 0.32, 0.36, 0.25, 0.03, 0.02, 0.007, 0.005, 0.005, 0.003),
    ('Polytechnic',    'young',  0.07, 0.20, 0.38, 0.12, 0.12, 0.04,  0.03,  0.015, 0.005),
    ('Polytechnic',    'mid',    0.15, 0.17, 0.33, 0.12, 0.11, 0.04,  0.03,  0.015, 0.005),
    ('Polytechnic',    'senior', 0.18, 0.15, 0.30, 0.12, 0.12, 0.05,  0.04,  0.02,  0.005),
    ('Post_Secondary', 'young',  0.05, 0.10, 0.26, 0.15, 0.20, 0.08,  0.08,  0.04,  0.005),
    ('Post_Secondary', 'mid',    0.10, 0.08, 0.23, 0.15, 0.19, 0.09,  0.08,  0.05,  0.005),
    ('Post_Secondary', 'senior', 0.12, 0.07, 0.20, 0.14, 0.18, 0.10,  0.09,  0.06,  0.005),
    ('Secondary',      'young',  0.04, 0.06, 0.21, 0.14, 0.24, 0.11,  0.11,  0.06,  0.005),
    ('Secondary',      'mid',    0.08, 0.05, 0.18, 0.13, 0.23, 0.11,  0.11,  0.08,  0.005),
    ('Secondary',      'senior', 0.09, 0.04, 0.15, 0.12, 0.22, 0.12,  0.12,  0.11,  0.005),
    ('Primary',        'young',  0.03, 0.03, 0.12, 0.09, 0.25, 0.12,  0.15,  0.15,  0.005),
    ('Primary',        'mid',    0.04, 0.03, 0.12, 0.09, 0.25, 0.12,  0.15,  0.15,  0.005),
    ('Primary',        'senior', 0.05, 0.02, 0.08, 0.07, 0.21, 0.12,  0.15,  0.24,  0.005),
    ('No_Formal',      'young',  0.03, 0.02, 0.10, 0.08, 0.25, 0.12,  0.16,  0.18,  0.005),
    ('No_Formal',      'mid',    0.03, 0.02, 0.10, 0.08, 0.25, 0.12,  0.16,  0.18,  0.005),
    ('No_Formal',      'senior', 0.04, 0.02, 0.07, 0.06, 0.21, 0.12,  0.16,  0.26,  0.005)
  ) AS t(edu, bucket, p1, p2, p3, p4, p5, p6, p7, p8, p9)
),
-- Normalize probabilities (some rows don't sum to 1.0)
cpt_norm AS (
  SELECT edu, bucket,
    p1/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p1,
    p2/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p2,
    p3/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p3,
    p4/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p4,
    p5/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p5,
    p6/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p6,
    p7/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p7,
    p8/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p8,
    p9/(p1+p2+p3+p4+p5+p6+p7+p8+p9) AS p9
  FROM cpt
),
eligible AS (
  SELECT agent_id, education_level,
    CASE
      WHEN age < 35 THEN 'young'
      WHEN age < 50 THEN 'mid'
      ELSE 'senior'
    END AS bucket,
    random() AS r
  FROM agents
  WHERE occupation IS NOT NULL
    AND occupation != ''
    AND occupation NOT IN (
      'Retired', 'Homemaker',
      'Infant/Toddler', 'Pre-school Student',
      'Primary School Student', 'Secondary School Student',
      'Post-Secondary Student', 'Student',
      'University Student', 'Polytechnic Student',
      'Unemployed', 'National Service',
      'Full-time National Serviceman'
    )
),
sampled AS (
  SELECT e.agent_id,
    CASE
      WHEN e.r < c.p1 THEN 'Senior Official or Manager'
      WHEN e.r < c.p1+c.p2 THEN 'Professional'
      WHEN e.r < c.p1+c.p2+c.p3 THEN 'Associate Professional or Technician'
      WHEN e.r < c.p1+c.p2+c.p3+c.p4 THEN 'Clerical Worker'
      WHEN e.r < c.p1+c.p2+c.p3+c.p4+c.p5 THEN 'Service or Sales Worker'
      WHEN e.r < c.p1+c.p2+c.p3+c.p4+c.p5+c.p6 THEN 'Production Craftsman or Related Worker'
      WHEN e.r < c.p1+c.p2+c.p3+c.p4+c.p5+c.p6+c.p7 THEN 'Plant or Machine Operator or Assembler'
      WHEN e.r < c.p1+c.p2+c.p3+c.p4+c.p5+c.p6+c.p7+c.p8 THEN 'Cleaner, Labourer or Related Worker'
      ELSE 'Agricultural or Fishery Worker'
    END AS new_occupation
  FROM eligible e
  LEFT JOIN cpt_norm c ON c.edu = e.education_level AND c.bucket = e.bucket
)
UPDATE agents a
SET occupation = COALESCE(s.new_occupation, a.occupation)
FROM sampled s
WHERE a.agent_id = s.agent_id;
