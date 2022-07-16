# Notes on charge data cleanup

## SURRENDER DEF BY SURETY (M) and (F)
There are two charges like this, one for felonies and one for misdemeanors. This is when the bondsman has turned the defendant back in. The docket number can be used to look up the original charge, but all we know from the jail data is whether it's a felony or misdemeanor. 

I'm setting the min/max_level to the full ranges of M or F, estimate to 1 and flag to 1. The flag is 1 because we can't tell whether it's violent or dwi without looking at the underlying charge.

There were 64 people with one of these over the first 6 months. Guessing that most were higher-level charges, but in any case it's a flag that something is an issue and we may not be surprised if they don't get out.

Charge IDs: 286, 316.

## Probation and pretrial violations
There are 7 probation and pretrial violations. I've set violation = 1 for all of them, but flag and estimate to 0 (and the levels are all 0).

It may be worth specifically investigating pretrial release violations - that's just one charge: id = 302. There were 213 people with this charge in the first 6 months.

Charge IDs: 273, 279, 293, 302, 304, 309, 315

## Use of "estimate"
Since I'm now giving the full range of possible levels, there's no need to use estimate for that, so I'll only use it if there's really some guessing going on. That mostly just 
applies to DWI which has a different sentencing system.

## Infractions
There are a fair number of infractions (traffic especially that are punished by fines or warning - setting to 0 and removing all flags)

## Non-support
There are 2 charges non-support (NON_SUPPORT and CIVIL OFA). I have set level to 0 and estimate to 0, but not_primary_custodian to 1

## Conspiracy
Set Felony Conspiracy (id=328) range as 4-12 (per statute could range from B2 to class 1 misd). Also set estimate (obviously) and flag = 1 because we can't tell if violent or not.

