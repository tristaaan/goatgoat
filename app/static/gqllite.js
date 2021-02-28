
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

function setCookie(key, value) {
  document.cookie = `${key}=${value}; expires=${Date.now() + (60 * 60 * 24 * 5)}`;
}

function getCookie(key) {
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith(`${key}=`))
    .split('=')[1];
  return cookieValue;
}

function deleteCookie(key) {
  document.cookie = `${key}=; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}