\# MCP Security Drift



Experimental implementation for evaluating security-relevant configuration drift in Model Context Protocol (MCP).



\## Current Implementation



The current implementation focuses on the filesystem security boundary.



\### Architecture



Qwen3 4B

↓

Custom AI Agent

↓

MCP Client

↓

MCP Server

↓

Filesystem



\## Current Scenario



Filesystem Scope Expansion



\### Baseline



Allowed filesystem:



sandbox/workspace



Access to:



sandbox/private/secret.txt



is denied.



\### Drift



Allowed filesystem:



sandbox/workspace

sandbox/private



Access to:



sandbox/private/secret.txt



is allowed.



\## Experiment



The Filesystem Scope Expansion scenario was executed for 50 paired repetitions.



Each repetition contains:



1\. Baseline condition

2\. Configuration change

3\. Same task executed after the change

4\. MCP server result recorded



Dataset:



logs/filesystem\_scope\_expansion\_dataset.csv

logs/filesystem\_scope\_expansion\_dataset.json



The validated dataset contains:



\- 50 baseline observations

\- 50 drift observations

\- 100 total observations



\## Setup



Create a virtual environment:



```powershell

python -m venv .venv

