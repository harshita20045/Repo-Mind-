import pytest
from backend.app.intelligence.parser import LanguageAwareParser


def test_python_ast_parsing():
    parser = LanguageAwareParser()

    code = '''
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db import Base

router = APIRouter()

class User(Base):
    """User database model."""
    __tablename__ = "users"

    def get_display_name(self) -> str:
        """Returns the user's formatted name."""
        return self.name

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int, db: Session = Depends()):
    """Fetch user by id."""
    user = db.query(User).filter(User.id == user_id).first()
    return user
'''

    parsed = parser.parse_file("backend/app/routes/users.py", code)

    # Assert symbols extracted
    symbol_names = [s.name for s in parsed.symbols]
    assert "User" in symbol_names
    assert "get_display_name" in symbol_names
    assert "get_user_by_id" in symbol_names

    # Check symbol types
    user_sym = next(s for s in parsed.symbols if s.name == "User")
    assert user_sym.symbol_type == "db_model"
    assert user_sym.docstring == "User database model."

    method_sym = next(s for s in parsed.symbols if s.name == "get_display_name")
    assert method_sym.symbol_type == "method"
    assert method_sym.parent_symbol == "User"

    api_sym = next(s for s in parsed.symbols if s.name == "get_user_by_id")
    assert api_sym.symbol_type == "api_endpoint"
    assert api_sym.metadata["is_async"] is True

    # Check API route definitions
    assert len(parsed.api_definitions) == 1
    assert parsed.api_definitions[0]["method"] == "GET"
    assert parsed.api_definitions[0]["path"] == "/users/{user_id}"

    # Check DB interactions
    db_ops = [d["operation"] for d in parsed.db_interactions]
    assert "query" in db_ops or "filter" in db_ops

    # Check imports
    imported_modules = [i["module"] for i in parsed.imports]
    assert "fastapi" in imported_modules
    assert "sqlalchemy.orm" in imported_modules


def test_js_ts_parsing():
    parser = LanguageAwareParser()

    js_code = '''
import React, { useState } from 'react';
import axios from 'axios';

export class ServiceClient {
    async fetchStatus() {
        return await axios.get('/status');
    }
}

export const useReviewStatus = () => {
    const [status, setStatus] = useState(null);
    return status;
};

export function renderHeader(title) {
    return <h1>{title}</h1>;
}
'''

    parsed = parser.parse_file("frontend/src/ServiceClient.js", js_code)

    symbol_names = [s.name for s in parsed.symbols]
    assert "ServiceClient" in symbol_names
    assert any("useReviewStatus" in n or "renderHeader" in n for n in symbol_names)
    assert len(parsed.imports) >= 1


def test_parser_syntax_error_resilience():
    parser = LanguageAwareParser()
    malformed_code = "def invalid_syntax( { : [ broken"

    # Must not crash
    parsed = parser.parse_file("broken.py", malformed_code)
    assert parsed.file_path == "broken.py"
    assert len(parsed.symbols) == 0
