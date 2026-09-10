# Core Components Overview

```text
# Related Code
- `path/to/file`
```

## Component Dictionary

- openclaw: [responsibility]
- .claude: [responsibility]
- front: [responsibility]
- knowledgegraph: [responsibility]
- lsydata: [responsibility]
- 后端开发: [responsibility]

## Relationship Graph
```mermaid
graph TD
core[openclaw]
_claude[.claude]
core --> _claude
front[front]
core --> front
knowledgegraph[knowledgegraph]
core --> knowledgegraph
lsydata[lsydata]
core --> lsydata
____[后端开发]
core --> ____
```
