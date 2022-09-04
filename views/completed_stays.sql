-- View: jaildata.completed_stays

-- DROP MATERIALIZED VIEW jaildata.completed_stays;

CREATE MATERIALIZED VIEW jaildata.completed_stays
TABLESPACE pg_default
AS
 SELECT s.defendant_id,
    s.name,
    s.gender,
    s.race,
    s.start_date,
    s.end_date,
    s.days,
    c.min_level,
    c.max_level,
    c.has_violation,
    c.violent,
    c.dwi,
    c.not_primary_custodian,
        CASE
            WHEN b.total_secured IS NULL THEN 0::bigint
            ELSE b.total_secured / 100
        END AS total_secured_bond,
    b.has_nobond,
    s.last_id,
    c.is_pretrial
   FROM stay_days s
     LEFT JOIN charges_summary c ON s.last_id = c.defendant_id
     LEFT JOIN bond_summary b ON s.last_id = b.defendant_id
WITH DATA;

ALTER TABLE jaildata.completed_stays
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.completed_stays TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.completed_stays TO u3qe7k9o5epmig;
