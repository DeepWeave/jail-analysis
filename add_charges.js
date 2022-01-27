require('dotenv').config({ path: './.env' })
const { knex } = require('./util/db');
// const { searchCourtRecords } = require('../search-court-records');
// const { addCases } = require('../util/subscribe');
const { logger } = require('./util/logger');
const { searchCourtRecords } = require('./util/search-court-records');

/*
select id, defendant_id, name, gender, race, end_date, 
		DATE_PART('day', '2022-01-21 00:00:00'::timestamp - end_date) as count
	from jaildata.stays where use_flag = 1 and end_date is not null 
		and DATE_PART('day', '2022-01-21 00:00:00'::timestamp - end_date) = 2
*/
async function doit() {
  const d = new Date()
  const today = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();

  const stays = await knex('jaildata.stays')
    .select('id', 'defendant_id', 'name', 'gender', 'race', 'end_date')
     .whereNotNull('end_date').where('use_flag', 1)
     .whereRaw("DATE_PART('day', '" + today + "'::timestamp - end_date) = 2")

  for (let i = 0; i<stays.length; ++i) {
    let nms = stays[i]['name'].split(' ')
    console.log(nms)
    const lastName = nms[0].trim().replace(',','')
    const firstName = nms[1].trim()

    const lookup = {
      lastName,
      firstName,
    }
    console.log(lookup)
    const matches = await searchCourtRecords(lookup, null)
    console.log("CASES!!!")
    console.log(JSON.stringify(matches))
  }
  logger.debug('Record count = ' + stays.length)
  return
}



(async() => {
  logger.debug('Call doit');
  await doit();
  logger.debug('Done with doit');
  process.exit();
})();
