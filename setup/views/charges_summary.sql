-- View: jaildata.charges_summary

-- DROP VIEW jaildata.charges_summary;

CREATE OR REPLACE VIEW jaildata.charges_summary
 AS
 SELECT b.defendant_id,
    min(b.rank) AS min_level,
    max(b.rank) AS max_level,
    max(b.violation) AS has_violation,
    max(b.violent) AS violent,
    max(b.dwi) AS dwi,
    max(b.not_primary_custodian) AS not_primary_custodian,
    min(b.is_pretrial) AS is_pretrial
   FROM daily_charges_coded b
  GROUP BY b.defendant_id;

ALTER TABLE jaildata.charges_summary
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.charges_summary TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.charges_summary TO u3qe7k9o5epmig;

