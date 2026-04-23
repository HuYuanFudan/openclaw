<template>
    <div ref="graph" class="graph"></div>
  </template>
  
  <script>
  import * as d3 from 'd3';
  
  export default {
    name: 'KnowledgeGraph',
    mounted() {
      this.fetchGraphData();
    },
    methods: {
      fetchGraphData() {
        const query = `
          MATCH (n:Company)-[r]->(m:Company)
          RETURN n, r, m
        `;
  
        fetch('http://localhost:7474/db/data/transaction/commit', {
          method: 'POST',
          headers: {
            'Authorization': 'Basic ' + btoa('neo4j:1598273166wsy.'),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ statements: [{ statement: query }] }),
        })
        .then(response => response.json())
        .then(data => {
          const nodes = this.processNodes(data);
          const links = this.processLinks(data);
          this.drawGraph(nodes, links);
        });
      },
      processNodes(data) {
        const nodes = [];
        // eslint-disable-next-line
        data.results[0].columns.forEach(column => {
        });
        return nodes;
      },
      processLinks(data) {
        const links = [];
        // eslint-disable-next-line
        data.results[0].columns.forEach(column => {
        });
        return links;
      },
      drawGraph(nodes, links) {
        const svg = d3.select(this.$refs.graph)
                      .append('svg')
                      .attr('width', 800)
                      .attr('height', 600);
  
        svg.selectAll('line')
           .data(links)
           .enter()
           .append('line')
           .attr('x1', d => d.source.x)
           .attr('y1', d => d.source.y)
           .attr('x2', d => d.target.x)
           .attr('y2', d => d.target.y)
           .style('stroke', 'black');
  
        // eslint-disable-next-line
        const node = svg.selectAll('circle')
                        .data(nodes)
                        .enter()
                        .append('circle')
                        .attr('cx', d => d.x)
                        .attr('cy', d => d.y)
                        .attr('r', 5)
                        .style('fill', 'blue')
                        .on('click', d => {
                          alert(`Clicked on node: ${d.id}`);
                        });
      }
    }
  }
  </script>
  
  <style scoped>
  .graph {
    width: 800px;
    height: 600px;
  }
  </style>
  