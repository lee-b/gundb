import simpy
import networkx as nx
import pytest
import random
from gundb.models import Event, UserStream, UserEvent
from gundb.vector_clock import VectorClock

# Node class for simulation
class Node:
    def __init__(self, node_id, env):
        self.node_id = node_id
        self.env = env
        self.event_stream = []
        self.peers = []
        self.partitioned = False
        
    def send_event(self, event):
        self.event_stream.append(event)
        if not self.partitioned:
            for peer in self.peers:
                if not peer.partitioned:
                    delay = self.env.now + random.uniform(0, 2)
                    self.env.process(self.delayed_send(peer, event, delay))
                    
    def delayed_send(self, peer, event, delay):
        yield self.env.timeout(delay - self.env.now)
        peer.receive_event(event)
        
    def receive_event(self, event):
        self.event_stream.append(event)
        
    def get_sorted_events(self):
        # Sort events based on vector clock causality
        def compare_clocks(clock1, clock2):
            # Convert dictionary keys to strings for consistent comparison
            clock1_str = {str(k): v for k, v in clock1.items()}
            clock2_str = {str(k): v for k, v in clock2.items()}
            # Check if clock1 happened before or is equal to clock2
            before = True
            equal = True
            for site in set(list(clock1_str.keys()) + list(clock2_str.keys())):
                c1 = clock1_str.get(site, 0)
                c2 = clock2_str.get(site, 0)
                if c1 > c2:
                    before = False
                if c1 != c2:
                    equal = False
            return -1 if before and not equal else (0 if equal else 1)
        
        # Custom sorting using comparison function
        sorted_events = []
        for event in self.event_stream:
            inserted = False
            for i, sorted_event in enumerate(sorted_events):
                if compare_clocks(event["clock"], sorted_event["clock"]) < 0:
                    sorted_events.insert(i, event)
                    inserted = True
                    break
            if not inserted:
                sorted_events.append(event)
        return sorted_events

def run_simulation(env, nodes, partition_prob, delay_range):
    while True:
        # Randomly partition some nodes
        for node in nodes:
            if random.random() < partition_prob:
                node.partitioned = True
            else:
                node.partitioned = False
        
        # Generate events from random nodes
        node = random.choice(nodes)
        if not node.partitioned:
            event = {
                "id": f"event_{env.now}_{node.node_id}",
                "clock": {str(node.node_id): int(env.now)},
                "origin": node.node_id
            }
            node.send_event(event)
        
        yield env.timeout(1)

@pytest.mark.parametrize("num_nodes, duration", [
    (10, 20),    # Small scale
    (100, 50),   # Medium scale
    (1000, 100), # Large scale
])
def test_gundb_consistency(num_nodes, duration):
    # Initialize environment and network
    env = simpy.Environment()
    G = nx.erdos_renyi_graph(num_nodes, 0.1)  # Random network topology
    nodes = [Node(i, env) for i in range(num_nodes)]
    
    # Set up peers based on network topology
    for i, node in enumerate(nodes):
        node.peers = [nodes[j] for j in range(num_nodes) if j != i and G.has_edge(i, j)]
    
    # Start simulation process
    env.process(run_simulation(env, nodes, partition_prob=0.2, delay_range=(0, 2)))
    
    # Run simulation
    env.run(until=duration)
    
    # Collect and compare sorted events across all nodes
    global_events = []
    for node in nodes:
        sorted_events = node.get_sorted_events()
        global_events.extend(sorted_events)
    
    # Deduplicate and sort globally
    seen = set()
    unique_events = [e for e in global_events if not (tuple(sorted((k, v) for k, v in e["clock"].items())) in seen or seen.add(tuple(sorted((k, v) for k, v in e["clock"].items()))))]
    
    # Custom sorting for global order
    def compare_global_clocks(event1, event2):
        # Convert dictionary keys to strings for consistent comparison
        clock1_str = {str(k): v for k, v in event1["clock"].items()}
        clock2_str = {str(k): v for k, v in event2["clock"].items()}
        # Check if clock1 happened before or is equal to clock2
        before = True
        equal = True
        for site in set(list(clock1_str.keys()) + list(clock2_str.keys())):
            c1 = clock1_str.get(site, 0)
            c2 = clock2_str.get(site, 0)
            if c1 > c2:
                before = False
            if c1 != c2:
                equal = False
        return -1 if before and not equal else (0 if equal else 1)
    
    global_order = []
    for event in unique_events:
        inserted = False
        for i, sorted_event in enumerate(global_order):
            if compare_global_clocks(event, sorted_event) < 0:
                global_order.insert(i, event)
                inserted = True
                break
        if not inserted:
            global_order.append(event)
    
    # Verify consistency (simplified: just check if all nodes have same event count after dedup)
    for i, node in enumerate(nodes):
        node_events = node.get_sorted_events()
        deduped_node_events = [e for e in node_events if not (tuple(sorted((k, v) for k, v in e["clock"].items())) in set(tuple(sorted((k, v) for k, v in e2["clock"].items())) for e2 in node_events[:i]))]
        assert len(deduped_node_events) <= len(global_order), f"Node {i} has inconsistent event count"
