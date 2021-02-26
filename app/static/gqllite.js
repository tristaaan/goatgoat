
async function sendQuery(query, variables = null, operationName = null) {
  const res = await fetch('/graphql-api', {
    method: 'POST',
    accept: 'application/json',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables, operationName })
  });
  const json = await res.json();
  if (json.errors) {
    throw json;
  }
  return json;
}