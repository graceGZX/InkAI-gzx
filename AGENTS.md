# Project Working Notes

- When a GitHub or remote Git operation cannot connect or times out, first run:
  `export https_proxy=http://proxy.nioint.com:8080/`
  `export http_proxy=http://proxy.nioint.com:8080/`
  Then retry the Git operation in the same shell environment.
