def create_blank_structure():
        return {
            "status": "active",
            "projects": [{
                "id": None, 
                "projectCode": None, 
                "projectName": None,
                "description": None,
                "priority": None,
                "category": None,
                "projectType": None,
                "location": {"district": None, "street": None, "startPoint": None},
                "scope": {"length": None, "width": None, "materialSummary": None},
                "dates": {"plannedStart": None, "plannedEnd": None, "duration": None},
                "budget": {"total": None, "used": "0", "remaining": None, "currency": "TRY"},
                "team": {"projectManager": {"name": None, "phone": None}, "assignedTeams": []},
                "lastUpdate": None,
                "detail": {}
            }]
        }