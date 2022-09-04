-- View: jaildata.bond_summary

-- DROP VIEW jaildata.bond_summary;

CREATE OR REPLACE VIEW jaildata.bond_summary
 AS
 SELECT x.defendant_id,
    s.total_secured,
        CASE
            WHEN n.has_nobond IS NULL THEN 0
            ELSE 1
        END AS has_nobond
   FROM ( SELECT daily_charges.defendant_id,
            count(daily_charges.charge) AS n_charges
           FROM daily_charges
          GROUP BY daily_charges.defendant_id) x
     LEFT JOIN ( SELECT b.defendant_id,
            sum(b.bond_amount) AS total_secured
           FROM daily_charges b
          WHERE b.bond_status::text = 'ACTI'::text AND (b.bond_type::text = 'SECURED'::text OR b.bond_type IS NULL)
          GROUP BY b.defendant_id) s ON x.defendant_id = s.defendant_id
     LEFT JOIN ( SELECT b.defendant_id,
            count(b.defendant_id) AS has_nobond
           FROM daily_charges b
          WHERE b.bond_status::text = 'ACTI'::text AND b.bond_type::text = 'NO BOND'::text
          GROUP BY b.defendant_id) n ON x.defendant_id = n.defendant_id;

ALTER TABLE jaildata.bond_summary
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.bond_summary TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.bond_summary TO u3qe7k9o5epmig;

