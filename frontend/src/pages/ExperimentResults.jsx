import React, { useEffect, useState } from "react";
import { Card, Table, Tag, Typography, message } from "antd";
import { getHealth } from "../api";

const { Title } = Typography;

function ExperimentResults() {
  const [results, setResults] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    getHealth().then((r) => setHealth(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      <Title level={3}>Experiment Results</Title>
      <Card>
        <p>Run the experiment framework first, then results will appear here.</p>
        {health && <Tag color="green">Backend: v{health.version}</Tag>}
      </Card>
    </div>
  );
}

export default ExperimentResults;