import pytest
from backend.app.intelligence.parser import LanguageAwareParser
from backend.app.intelligence.graph import CodeKnowledgeGraph
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.organizations.models import Project, Repository
from backend.app.auth.models import Organization


def test_knowledge_graph_construction_and_mermaid():
    parser = LanguageAwareParser()

    file1 = (
        "from backend.app.service import process_data\n"
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.post('/process')\n"
        "def handle_process():\n"
        "    return process_data()\n"
    )

    file2 = (
        "def process_data():\n"
        "    return 'processed'\n"
    )

    pf1 = parser.parse_file("backend/app/routes/api.py", file1)
    pf2 = parser.parse_file("backend/app/service.py", file2)

    graph = CodeKnowledgeGraph(repository_id=1)
    graph.build_from_parsed_files([pf1, pf2])

    # Check nodes
    node_keys = list(graph.graph.nodes)
    assert any("file:backend/app/routes/api.py" in k for k in node_keys)
    assert any("file:backend/app/service.py" in k for k in node_keys)
    assert any("api:POST:/process" in k for k in node_keys)
    assert any("fn:backend/app/service.py:process_data" in k for k in node_keys)

    # Check edges
    edges = list(graph.graph.edges(data=True))
    assert len(edges) > 0
    rel_types = [d.get("relation_type") for _, _, d in edges]
    assert "contains" in rel_types

    # Generate Mermaid diagram
    diagram = graph.generate_mermaid_diagram()
    assert "flowchart TD" in diagram
    assert len(diagram.splitlines()) > 1


def test_knowledge_graph_persistence(db_session):
    org = Organization(name="Test Org Graph")
    db_session.add(org)
    db_session.commit()

    proj = Project(organization_id=org.id, name="Test Proj Graph")
    db_session.add(proj)
    db_session.commit()

    repo = Repository(
        project_id=proj.id,
        github_owner="test",
        github_name="repo_graph",
        github_repository_id="99901",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.commit()

    parser = LanguageAwareParser()
    code = (
        "class OrderService:\n"
        "    def create_order(self):\n"
        "        pass\n"
    )
    pf = parser.parse_file("services/order.py", code)

    kg = CodeKnowledgeGraph(repository_id=repo.id)
    kg.build_from_parsed_files([pf])
    node_count, edge_count = kg.persist(db_session)

    assert node_count > 0

    # Query directly from DB
    saved_nodes = db_session.query(CodeGraphNode).filter(CodeGraphNode.repository_id == repo.id).all()
    assert len(saved_nodes) == node_count

    saved_edges = db_session.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == repo.id).all()
    assert len(saved_edges) == edge_count
