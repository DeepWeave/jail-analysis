-- View: jaildata.stay_days

-- DROP VIEW jaildata.stay_days;

CREATE OR REPLACE VIEW jaildata.stay_days
 AS
 SELECT s.id,
    s.defendant_id,
    s.name,
    s.gender,
    s.race,
    s.start_date,
    s.end_date,
    s.days,
    f.last_id
   FROM ( SELECT stays.id,
            stays.defendant_id,
            stays.name,
            stays.gender,
            stays.race,
            stays.start_date,
            stays.end_date,
            date_part('day'::text, stays.end_date::timestamp without time zone - stays.start_date::timestamp without time zone) + 1::double precision AS days
           FROM stays
          WHERE stays.use_flag = 1 AND stays.end_date IS NOT NULL) s
     LEFT JOIN final_defendant_id f ON s.defendant_id = f.defendant_id;

ALTER TABLE jaildata.stay_days
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.stay_days TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.stay_days TO u3qe7k9o5epmig;

