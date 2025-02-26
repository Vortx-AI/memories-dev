Deployment
==========

.. code-block:: text
   
Overview
--------

The memories-dev framework supports multiple deployment patterns to accommodate different scalability, reliability, and performance requirements. This guide covers the three main deployment patterns: Standalone, Consensus, and Swarmed.

Deployment Patterns
-------------------

1. **Standalone Deployment**
   - Single-node deployment
   - Simplest configuration
   - Suitable for development and small-scale applications
   - Limited scalability and fault tolerance

2. **Consensus Deployment**
   - Multi-node deployment with consensus algorithm
   - Strong consistency guarantees
   - Suitable for applications requiring reliable state management
   - Moderate scalability (typically 3-7 nodes)

3. **Swarmed Deployment**
   - Highly distributed deployment
   - Designed for maximum scalability
   - Suitable for large-scale production applications
   - Eventual consistency model

Cloud Providers
---------------

The framework supports deployment on major cloud providers:

- **AWS**: Amazon Web Services
- **GCP**: Google Cloud Platform
- **Azure**: Microsoft Azure

Standalone Deployment
---------------------

The simplest deployment pattern, ideal for development and testing:

.. code-block:: python

    from memories.deployments.standalone import StandaloneDeployment
    
    # Configure AWS standalone deployment
    aws_deployment = StandaloneDeployment(
        provider="aws",
        config={
            "instance_type": "t3.xlarge",
            "region": "us-west-2",
            "zone": "us-west-2a",
            "storage": {
                "size": 100,  # GB
                "type": "gp3"
            },
            "network": {
                "public_ip": True
            }
        }
    )
    
    # Deploy the system
    deployment_result = aws_deployment.deploy()
    
    print(f"Deployment ID: {deployment_result['deployment_id']}")
    print(f"Instance ID: {deployment_result['instance_id']}")
    print(f"Public IP: {deployment_result['public_ip']}")
    print(f"Status: {deployment_result['status']}")

Example Output:

.. code-block:: text

    Deployment ID: standalone-aws-20240225-123456
    Instance ID: i-0abc123def456789
    Public IP: 54.123.45.67
    Status: running

Consensus Deployment
--------------------

For applications requiring strong consistency:

.. code-block:: python

    from memories.deployments.consensus import ConsensusDeployment
    
    # Configure GCP consensus deployment
    gcp_deployment = ConsensusDeployment(
        provider="gcp",
        config={
            "consensus": {
                "algorithm": "raft",
                "min_nodes": 3,
                "max_nodes": 5,
                "quorum_size": 2
            },
            "node_specs": [
                {
                    "id": "node1",
                    "machine_type": "n2-standard-2",
                    "zone": "us-west1-a"
                },
                {
                    "id": "node2",
                    "machine_type": "n2-standard-2",
                    "zone": "us-west1-b"
                },
                {
                    "id": "node3",
                    "machine_type": "n2-standard-2",
                    "zone": "us-west1-c"
                }
            ],
            "network": {
                "vpc_name": "consensus-vpc",
                "subnet_name": "consensus-subnet"
            }
        }
    )
    
    # Deploy the system
    deployment_result = gcp_deployment.deploy()
    
    print(f"Deployment ID: {deployment_result['deployment_id']}")
    print(f"Leader Node: {deployment_result['leader_node']}")
    print(f"Follower Nodes: {', '.join(deployment_result['follower_nodes'])}")
    print(f"Status: {deployment_result['status']}")
    
    # Monitor the consensus cluster
    cluster_status = gcp_deployment.get_cluster_status()
    print(f"\nCluster Status:")
    print(f"Leader: {cluster_status['leader']}")
    print(f"Term: {cluster_status['term']}")
    print(f"Committed Index: {cluster_status['committed_index']}")
    print(f"Applied Index: {cluster_status['applied_index']}")

Example Output:

.. code-block:: text

    Deployment ID: consensus-gcp-20240225-123456
    Leader Node: node1
    Follower Nodes: node2, node3
    Status: running
    
    Cluster Status:
    Leader: node1
    Term: 1
    Committed Index: 42
    Applied Index: 42

Swarmed Deployment
------------------

For highly scalable applications:

.. code-block:: python

    from memories.deployments.swarmed import SwarmedDeployment
    
    # Configure Azure swarmed deployment
    azure_deployment = SwarmedDeployment(
        provider="azure",
        config={
            "swarm": {
                "min_nodes": 3,
                "max_nodes": 10,
                "manager_nodes": 3,
                "worker_nodes": 5
            },
            "node_specs": {
                "manager_specs": {
                    "vm_size": "Standard_D2s_v3",
                    "storage_size": 100
                },
                "worker_specs": {
                    "vm_size": "Standard_D4s_v3",
                    "storage_size": 200
                }
            },
            "network": {
                "vnet_name": "swarmed-vnet",
                "subnet_name": "swarmed-subnet",
                "resource_group": "swarmed-rg",
                "location": "westus2"
            },
            "scaling": {
                "target_cpu_utilization": 70,
                "scale_up_cooldown": 300,
                "scale_down_cooldown": 300
            }
        }
    )
    
    # Deploy the system
    deployment_result = azure_deployment.deploy()
    
    print(f"Deployment ID: {deployment_result['deployment_id']}")
    print(f"Manager Nodes: {', '.join(deployment_result['manager_nodes'])}")
    print(f"Worker Nodes: {', '.join(deployment_result['worker_nodes'])}")
    print(f"Status: {deployment_result['status']}")
    
    # Scale the swarm
    scaling_result = azure_deployment.scale(worker_nodes=8)
    
    print(f"\nScaling Result:")
    print(f"New Worker Count: {scaling_result['worker_count']}")
    print(f"Scaling Status: {scaling_result['status']}")
    
    # Get swarm services
    services = azure_deployment.get_services()
    
    print(f"\nSwarm Services:")
    for service in services:
        print(f"- {service['name']}: {service['replicas']} replicas, {service['status']}")

Example Output:

.. code-block:: text

    Deployment ID: swarmed-azure-20240225-123456
    Manager Nodes: manager-1, manager-2, manager-3
    Worker Nodes: worker-1, worker-2, worker-3, worker-4, worker-5
    Status: running
    
    Scaling Result:
    New Worker Count: 8
    Scaling Status: scaling
    
    Swarm Services:
    - memories-api: 3 replicas, running
    - memories-worker: 5 replicas, running
    - memories-db: 1 replicas, running

Advanced Configuration
----------------------

Custom Hardware Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify custom hardware requirements:

.. code-block:: python

    from memories.deployments.standalone import StandaloneDeployment
    
    # Configure deployment with custom hardware
    deployment = StandaloneDeployment(
        provider="aws",
        config={
            "instance_type": "g4dn.xlarge",  # GPU instance
            "region": "us-west-2",
            "hardware": {
                "cpu": {
                    "vcpus": 4,
                    "architecture": "x86_64"
                },
                "memory": {
                    "ram": 16,
                    "swap": 4
                },
                "storage": {
                    "root_volume": {
                        "size": 100,
                        "type": "gp3",
                        "iops": 3000,
                        "throughput": 125
                    },
                    "data_volume": {
                        "size": 500,
                        "type": "gp3",
                        "iops": 6000,
                        "throughput": 250
                    }
                },
                "gpu": {
                    "type": "nvidia_tesla_t4",
                    "count": 1,
                    "memory": 16
                }
            }
        }
    )
    
    # Deploy with custom hardware
    deployment_result = deployment.deploy()

Network Configuration
~~~~~~~~~~~~~~~~~~~~~

Configure network settings:

.. code-block:: python

    from memories.deployments.consensus import ConsensusDeployment
    
    # Configure deployment with custom network
    deployment = ConsensusDeployment(
        provider="gcp",
        config={
            "consensus": {
                "algorithm": "raft",
                "min_nodes": 3,
                "max_nodes": 5
            },
            "node_specs": [
                {"id": "node1", "machine_type": "n2-standard-2", "zone": "us-west1-a"},
                {"id": "node2", "machine_type": "n2-standard-2", "zone": "us-west1-b"},
                {"id": "node3", "machine_type": "n2-standard-2", "zone": "us-west1-c"}
            ],
            "network": {
                "vpc_name": "consensus-vpc",
                "subnet_name": "consensus-subnet",
                "firewall_name": "consensus-fw",
                "project_id": "my-project",
                "region": "us-west1",
                "cidr": "10.0.0.0/16",
                "subnets": {
                    "public": {
                        "enabled": True,
                        "cidr": "10.0.1.0/24",
                        "region": "us-west1"
                    },
                    "private": {
                        "enabled": True,
                        "cidr": "10.0.2.0/24",
                        "region": "us-west1"
                    }
                },
                "security": {
                    "rules": [
                        {
                            "name": "allow-internal",
                            "protocol": "all",
                            "ports": [],
                            "source_ranges": ["10.0.0.0/16"]
                        },
                        {
                            "name": "allow-ssh",
                            "protocol": "tcp",
                            "ports": ["22"],
                            "source_ranges": ["0.0.0.0/0"]
                        },
                        {
                            "name": "allow-api",
                            "protocol": "tcp",
                            "ports": ["8000"],
                            "source_ranges": ["0.0.0.0/0"]
                        }
                    ]
                }
            }
        }
    )
    
    # Deploy with custom network
    deployment_result = deployment.deploy()

Monitoring and Logging
~~~~~~~~~~~~~~~~~~~~~~

Configure monitoring and logging:

.. code-block:: python

    from memories.deployments.standalone import StandaloneDeployment
    
    # Configure deployment with monitoring and logging
    deployment = StandaloneDeployment(
        provider="aws",
        config={
            "instance_type": "t3.xlarge",
            "region": "us-west-2",
            "monitoring": {
                "enabled": True,
                "metrics": [
                    "cpu_utilization",
                    "memory_usage",
                    "disk_io",
                    "network_traffic"
                ],
                "alerts": [
                    {
                        "type": "cpu",
                        "threshold": 80,
                        "duration": 300
                    },
                    {
                        "type": "memory",
                        "threshold": 85,
                        "duration": 300
                    }
                ]
            },
            "logging": {
                "level": "info",
                "retention_days": 30,
                "cloudwatch": {
                    "enabled": True,
                    "log_group": "/aws/standalone/instance"
                }
            }
        }
    )
    
    # Deploy with monitoring and logging
    deployment_result = deployment.deploy()
    
    # Get monitoring metrics
    metrics = deployment.get_metrics(
        metric_names=["cpu_utilization", "memory_usage"],
        start_time="2024-02-24T00:00:00Z",
        end_time="2024-02-25T00:00:00Z",
        period=300  # 5-minute intervals
    )
    
    print("\nMonitoring Metrics:")
    for metric_name, datapoints in metrics.items():
        print(f"\n{metric_name}:")
        for datapoint in datapoints[:3]:  # Show first 3 datapoints
            print(f"  {datapoint['timestamp']}: {datapoint['value']} {datapoint['unit']}")

Example Output:

.. code-block:: text

    Monitoring Metrics:
    
    cpu_utilization:
      2024-02-24T00:00:00Z: 12.5 Percent
      2024-02-24T00:05:00Z: 14.2 Percent
      2024-02-24T00:10:00Z: 10.8 Percent
    
    memory_usage:
      2024-02-24T00:00:00Z: 4.2 GB
      2024-02-24T00:05:00Z: 4.3 GB
      2024-02-24T00:10:00Z: 4.1 GB

Deployment Management
---------------------

Managing Existing Deployments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from memories.deployments import DeploymentManager
    
    # Initialize deployment manager
    manager = DeploymentManager()
    
    # List all deployments
    deployments = manager.list_deployments()
    
    print("Existing Deployments:")
    for deployment in deployments:
        print(f"- {deployment['id']}: {deployment['type']} on {deployment['provider']}, "
              f"status: {deployment['status']}")
    
    # Get details for a specific deployment
    deployment_id = deployments[0]['id']
    details = manager.get_deployment(deployment_id)
    
    print(f"\nDeployment Details for {deployment_id}:")
    print(f"Type: {details['type']}")
    print(f"Provider: {details['provider']}")
    print(f"Created: {details['created_at']}")
    print(f"Status: {details['status']}")
    print(f"Resources: {len(details['resources'])} resources")
    
    # Stop a deployment
    stop_result = manager.stop_deployment(deployment_id)
    print(f"\nStopped deployment {deployment_id}: {stop_result['status']}")
    
    # Start a deployment
    start_result = manager.start_deployment(deployment_id)
    print(f"\nStarted deployment {deployment_id}: {start_result['status']}")
    
    # Delete a deployment
    delete_result = manager.delete_deployment(deployment_id)
    print(f"\nDeleted deployment {deployment_id}: {delete_result['status']}")

Example Output:

.. code-block:: text

    Existing Deployments:
    - standalone-aws-20240225-123456: standalone on aws, status: running
    - consensus-gcp-20240224-789012: consensus on gcp, status: running
    - swarmed-azure-20240223-345678: swarmed on azure, status: stopped
    
    Deployment Details for standalone-aws-20240225-123456:
    Type: standalone
    Provider: aws
    Created: 2024-02-25T12:34:56Z
    Status: running
    Resources: 3 resources
    
    Stopped deployment standalone-aws-20240225-123456: stopped
    
    Started deployment standalone-aws-20240225-123456: starting
    
    Deleted deployment standalone-aws-20240225-123456: deleting

Best Practices
--------------

1. **Deployment Selection**:
   - Use Standalone for development and testing
   - Use Consensus for applications requiring strong consistency
   - Use Swarmed for applications requiring high scalability

2. **Resource Optimization**:
   - Right-size your instances based on workload
   - Use auto-scaling for variable workloads
   - Monitor resource usage and adjust as needed

3. **Security**:
   - Use private subnets for internal components
   - Implement proper firewall rules
   - Enable encryption for data at rest and in transit

4. **High Availability**:
   - Deploy across multiple availability zones
   - Implement proper backup and recovery procedures
   - Use health checks and auto-healing
   - Set up monitoring and alerting
   - Implement proper failover mechanisms
   - Configure load balancing for optimal distribution

.. mermaid::
    :align: center
    :caption: System Architecture Overview

    graph TD
        Client[Client Applications] --> API[API Gateway]
        API --> Server[Memories Server]
        Server --> Models[Model System]
        Server --> DataAcq[Data Acquisition]
        Models --> LocalModels[Local Models]
        Models --> APIModels[API-based Models]
        DataAcq --> VectorData[Vector Data Sources]
        DataAcq --> SatelliteData[Satellite Data]
        Server --> Storage[Persistent Storage]

        classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
        classDef highlight fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
        
        class Client,API highlight;
        class Server,Models,DataAcq,Storage default; 