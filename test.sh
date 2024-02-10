#!/usr/bin/env sh

curl='curl --get --silent --verbose'
base_url='http://localhost:8000'
http_bin_url=https://httpbin.org/status/200

# Test Roxy

response=$($curl --data-urlencode "url=$http_bin_url" "$base_url/roxy")

# Test Roxy status
test "$(
  echo "$response" | jq '.headers["X-Roxy-Status"]'
)" = 200 || exit 1

# Test Roxy URL
test "$(
  echo "$response" | jq --raw-output '.headers["X-Roxy-Url"]'
)" = "$http_bin_url" || exit 1

# Test JSONP output
test "$(
  $curl --data-urlencode "url=$http_bin_url" "$base_url/roxy?callback=evaluate" | sed --quiet '/^evaluate(.*)$/p'
)" || exit 1

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
  echo "$response" | jq --raw-output .[0].url
)" = 'http://host.dom' || exit 1

# The first item should have 3 hits
test "$(
  echo "$response" | jq .[0].hits
)" = 3 || exit 1

# Clean up
$curl "$base_url/tasks/ferris?group=$group" > /dev/null
