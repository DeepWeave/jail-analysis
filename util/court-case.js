function CourtCase([
  court,
  county,
  defendant,
  dob,
  courtDate,
  courtRoom,
  session,
  [caseNumber, caseDetailsUri],
  citationNumber,
]) {
  const caseDetailsURLPrefix = `http://www1.aoc.state.nc.us`;

  const generateLinkToCaseDetails = (uri) => {
    return caseDetailsURLPrefix + uri;
  };

  return {
    court,
    county,
    defendant,
    dob,
    courtDate,
    courtRoom,
    session,
    caseNumber,
    linkToCaseDetails: generateLinkToCaseDetails(caseDetailsUri),
    citationNumber,
  };
}

module.exports = {
  CourtCase
}