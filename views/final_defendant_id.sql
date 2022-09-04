-- View: jaildata.final_defendant_id

-- DROP VIEW jaildata.final_defendant_id;

CREATE OR REPLACE VIEW jaildata.final_defendant_id
 AS
 SELECT s.start_date,
    s.defendant_id,
    s.name,
    s.gender,
    s.race,
    max(d.id) AS last_id
   FROM stays s
     LEFT JOIN daily_inmates d ON s.name = d.name AND s.gender::text = d.gender::text AND s.race::text = d.race::text AND d.import_date >= s.start_date AND d.import_date <= s.end_date
  WHERE s.end_date IS NOT NULL
  GROUP BY s.name, s.gender, s.race, s.start_date, s.defendant_id
  ORDER BY s.name, s.start_date;

ALTER TABLE jaildata.final_defendant_id
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.final_defendant_id TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.final_defendant_id TO u3qe7k9o5epmig;

