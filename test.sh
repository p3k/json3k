#!/usr/bin/env sh

curl='curl --get --silent --verbose'
base_url='http://localhost:8000'

# example.org is reserved by IANA for exactly this kind of use (RFC 2606),
# so it is about as reliable a target as a free one gets
test_url=https://example.org/

# Test Roxy

response=$($curl --data-urlencode "url=$test_url" "$base_url/roxy")

# Test Roxy status
test "$(
  printf %s "$response" | jq '.headers["X-Roxy-Status"]'
)" = 200 || exit 1

# Test Roxy URL
test "$(
  printf %s "$response" | jq --raw-output '.headers["X-Roxy-Url"]'
)" = "$test_url" || exit 1

# Test JSONP output
test "$(
  $curl --data-urlencode "url=$test_url" "$base_url/roxy?callback=evaluate" | sed --quiet '/^evaluate(.*)$/p'
)" || exit 1

# Test Roxy restrictions (assumes `allow_private_hosts` is not set in `local.py`)

test "$(
  $curl --data-urlencode 'url=file:///etc/hostname' "$base_url/roxy" | jq '.headers["X-Roxy-Status"]'
)" = 400 || exit 1

test "$(
  $curl --data-urlencode "url=$base_url/" "$base_url/roxy" | jq '.headers["X-Roxy-Status"]'
)" = 403 || exit 1

# Test that cookies set by the proxied server do not end up at the client
# (postman-echo.com returns the query parameters as response headers, and
# also sets a couple of its own, which this test should strip just the same)
test "$(
  $curl --include --data-urlencode 'url=https://postman-echo.com/response-headers?Set-Cookie=a%3Db' "$base_url/roxy" | grep --count --ignore-case '^set-cookie:'
)" = 0 || exit 1

# Test Ferris

group=unit-tests

# Be sure the group is empty
$curl "$base_url/tasks/ferris?group=$group" > /dev/null

# This curl adds a URL to the group
ferris_curl="$curl --get --data-urlencode 'url=http://host.dom' '$base_url/ferris?group=$group'"

# Send the curl request, then there should be one item more – rinse and repeat
test "$(eval "$ferris_curl" | xargs)" = 1
test "$(eval "$ferris_curl" | xargs)" = 2
test "$(eval "$ferris_curl" | xargs)" = 3

# Verify the data
response=$($curl --get "$base_url/ferris?group=$group")

# The first item should have the added URL
test "$(
  printf %s "$response" | jq --raw-output .[0].url
)" = 'http://host.dom' || exit 1

# The first item should have 3 hits
test "$(
  printf %s "$response" | jq .[0].hits
)" = 3 || exit 1

# Groups are file names, so they must not point anywhere else
for bad_group in '../unit-tests' '/tmp/unit-tests' 'unit.tests'; do
  test "$(
    $curl --output /dev/null --write-out '%{http_code}' \
      --data-urlencode "group=$bad_group" --data-urlencode 'url=http://host.dom' \
      "$base_url/ferris"
  )" = 400 || exit 1
done

# The days query param overrides how far back referrers are shown

response=$($curl --get --data-urlencode 'days=1' "$base_url/ferris?group=$group")

test "$(
  printf %s "$response" | jq .[0].hits
)" = 3 || exit 1

# Out of range or non-numeric values are rejected rather than silently
# falling back to the default
for bad_days in 0 -1 366 abc; do
  test "$(
    $curl --output /dev/null --write-out '%{http_code}' \
      --data-urlencode "days=$bad_days" \
      "$base_url/ferris?group=$group"
  )" = 400 || exit 1
done

# Clean up
$curl "$base_url/tasks/ferris?group=$group" > /dev/null
