-- View: jaildata.multi_stay_counts

-- DROP VIEW jaildata.multi_stay_counts;

CREATE OR REPLACE VIEW jaildata.multi_stay_counts
 AS
 SELECT b.cnt AS nstays,
    count(b.cnt) AS count
   FROM ( SELECT a.name,
            min(a.days) AS min,
            max(a.days) AS max,
            string_agg(a.days::text, ','::text) AS string_agg,
            count(a.name) AS cnt
           FROM ( SELECT stays.name,
                    date_part('day'::text, stays.end_date::timestamp without time zone - stays.start_date::timestamp without time zone) AS days
                   FROM stays
                  WHERE stays.use_flag = 1 AND stays.end_date IS NOT NULL) a
          GROUP BY a.name) b
  WHERE b.cnt > 1
  GROUP BY b.cnt
  ORDER BY b.cnt DESC;

ALTER TABLE jaildata.multi_stay_counts
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.multi_stay_counts TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.multi_stay_counts TO u3qe7k9o5epmig;


