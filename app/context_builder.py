def build_context(findings: list[dict], task: str) -> str:
    """
    Build a deterministic, reviewable LLM context from selected findings.
    No raw documents. Evidence is immutable.
    
    Updated for Phase 8.2: evidence is now a list of normalized evidence entries.
    """

    header = (
        "SYSTEM:\n"
        "You are a security analysis assistant.\n"
        "You do NOT discover vulnerabilities.\n"
        "You only explain and suggest remediation for the findings provided.\n"
        "Do NOT invent facts. If uncertain, say so.\n\n"
    )

    body = ["FINDINGS:"]

    for f in sorted(findings, key=lambda x: (x["rule_id"], x["evidence"][0]["file"] if x["evidence"] else "")):
        # Evidence is now a list (Phase 8.2 normalized schema)
        evidence_list = f["evidence"]
        
        if not evidence_list:
            continue  # Skip findings with no evidence
        
        # Use first evidence entry for primary context (multiple entries supported)
        primary_evidence = evidence_list[0]
        
        # Build evidence section with normalized fields
        location = primary_evidence["location"]
        location_str = (
            f"{location['type']} {location['start']}"
            + (f"-{location['end']}" if location.get("end") else "")
        )
        
        body.append(
            f"- Rule ID: {f['rule_id']}\n"
            f"  Title: {f['title']}\n"
            f"  Category: {f['category']}\n"
            f"  Suggested Severity: {f['severity_suggested']}\n"
            f"  Evidence:\n"
            f"    File: {primary_evidence['file']}\n"
            f"    Location: {location_str}\n"
            f"    Snippet:\n"
            f"    {primary_evidence['snippet']}\n"
        )
        
        # Include additional evidence entries if present
        if len(evidence_list) > 1:
            for idx, additional_evidence in enumerate(evidence_list[1:], start=2):
                additional_location = additional_evidence["location"]
                additional_location_str = (
                    f"{additional_location['type']} {additional_location['start']}"
                    + (f"-{additional_location['end']}" if additional_location.get("end") else "")
                )
                body.append(
                    f"    Additional evidence {idx}:\n"
                    f"      File: {additional_evidence['file']}\n"
                    f"      Location: {additional_location_str}\n"
                )

    task_block = f"\nTASK:\n{task}\n"

    return header + "\n".join(body) + task_block
