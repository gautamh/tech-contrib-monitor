import pytest
from scripts.format_data import normalize_name, format_cluster_data, format_pac_data

# Sample raw data for testing
SAMPLE_INDIVIDUAL_CONTRIBUTIONS = [
    # Cluster 1: Google execs to a non-Google PAC
    {
        "contributor_name": "PICHAI, SUNDAR", "contributor_employer": "Google", "contribution_receipt_amount": 1000, 
        "contribution_receipt_date": "2025-01-15", "committee_id": "C123", "pdf_url": "url1",
        "committee": {"name": "A Good Cause PAC", "party_full": "DEMOCRATIC PARTY"}
    },
    {
        "contributor_name": "Kent Walker", "contributor_employer": "Google", "contribution_receipt_amount": 1500, 
        "contribution_receipt_date": "2025-01-16", "committee_id": "C123", "pdf_url": "url2",
        "committee": {"name": "A Good Cause PAC", "party_full": "DEMOCRATIC PARTY"}
    },
    # Cluster 2: Should be ignored (donations to own company PAC)
    {
        "contributor_name": "SMITH, BRADFORD L.", "contributor_employer": "Microsoft", "contribution_receipt_amount": 500, 
        "contribution_receipt_date": "2025-02-01", "committee_id": "C00227546", "pdf_url": "url3",
        "committee": {"name": "MSVPAC", "party_full": ""}
    },
    {
        "contributor_name": "Satya Nadella", "contributor_employer": "Microsoft", "contribution_receipt_amount": 500, 
        "contribution_receipt_date": "2025-02-02", "committee_id": "C00227546", "pdf_url": "url4",
        "committee": {"name": "MSVPAC", "party_full": ""}
    },
    # Not a cluster (only one person)
    {
        "contributor_name": "Zuckerberg, Mark", "contributor_employer": "Meta", "contribution_receipt_amount": 2000, 
        "contribution_receipt_date": "2025-03-10", "committee_id": "C456", "pdf_url": "url5",
        "committee": {"name": "Future Forward", "party_full": "DEMOCRATIC PARTY"}
    }
]

SAMPLE_PAC_EXPENDITURES = [
    # Valid contribution
    {
        "committee": {"name": "GOOGLE LLC NETPAC"},
        "recipient_committee": {"name": "TROY CARTER FOR CONGRESS", "party_full": "DEMOCRATIC PARTY"},
        "disbursement_amount": 1000.0, "disbursement_date": "2025-08-29", "disbursement_purpose_category": "CONTRIBUTIONS",
        "pdf_url": "url_pac1", "transaction_id": "1"
    },
    # Refund (should be ignored)
    {
        "committee": {"name": "GOOGLE LLC NETPAC"},
        "recipient_committee": {"name": "TROY CARTER FOR CONGRESS", "party_full": "DEMOCRATIC PARTY"},
        "disbursement_amount": -500.0, "disbursement_date": "2025-08-30", "disbursement_purpose_category": "CONTRIBUTIONS",
        "pdf_url": "url_pac2", "transaction_id": "2"
    },
    # Not a contribution
    {
        "committee": {"name": "GOOGLE LLC NETPAC"},
        "recipient_committee": {"name": "Some Vendor Inc"},
        "disbursement_amount": 250.0, "disbursement_date": "2025-08-15", "disbursement_purpose_category": "OTHER",
        "pdf_url": "url_pac3", "transaction_id": "3"
    }
]

# --- Tests for normalize_name --- #

@pytest.mark.parametrize("input_name, expected_output", [
    ("SMITH, BRADFORD L.", "bradford smith"),
    ("Bradford L. Smith", "bradford smith"),
    ("PICHAI, SUNDAR", "pichai sundar"),
    ("Mark Elliot Zuckerberg", "elliot mark zuckerberg"),
])
def test_normalize_name(input_name, expected_output):
    assert normalize_name(input_name) == expected_output

# --- Tests for format_cluster_data --- #
    
def test_format_cluster_data_splits_by_time_chaining():
    """Tests that clusters are split using chaining logic (max 30 days gap)."""
    data = [
        # Group 1: Continuous chain (Jan 1 -> Jan 25 -> Feb 20). 
        # Jan 1 to Jan 25 = 24 days (<=30) -> Linked
        # Jan 25 to Feb 20 = 26 days (<=30) -> Linked
        # Total span > 50 days, but chaining keeps them together.
        {
            "contributor_name": "Executive Alpha", "contributor_employer": "TechCorp", "contribution_receipt_amount": 100,
            "contribution_receipt_date": "2025-01-01", "committee_id": "C999", "pdf_url": "u1",
            "committee": {"name": "PAC A", "party_full": "DEM"}
        },
        {
            "contributor_name": "Executive Beta", "contributor_employer": "TechCorp", "contribution_receipt_amount": 100,
            "contribution_receipt_date": "2025-01-25", "committee_id": "C999", "pdf_url": "u2",
            "committee": {"name": "PAC A", "party_full": "DEM"}
        },
        {
            "contributor_name": "Executive Gamma", "contributor_employer": "TechCorp", "contribution_receipt_amount": 100,
            "contribution_receipt_date": "2025-02-20", "committee_id": "C999", "pdf_url": "u3",
            "committee": {"name": "PAC A", "party_full": "DEM"}
        },
        # Group 2: Break in chain (May 1 -> Jul 1). Gap > 30 days. Should be new cluster.
        {
            "contributor_name": "Executive Delta", "contributor_employer": "TechCorp", "contribution_receipt_amount": 100,
            "contribution_receipt_date": "2025-05-01", "committee_id": "C999", "pdf_url": "u4",
            "committee": {"name": "PAC A", "party_full": "DEM"}
        },
        {
            "contributor_name": "Executive Epsilon", "contributor_employer": "TechCorp", "contribution_receipt_amount": 100,
            "contribution_receipt_date": "2025-07-01", "committee_id": "C999", "pdf_url": "u5",
            "committee": {"name": "PAC A", "party_full": "DEM"}
        },
        # Exec F makes Group 2 a valid cluster (min 2 donors)
        {
            "contributor_name": "Executive Zeta", "contributor_employer": "TechCorp", "contribution_receipt_amount": 100,
            "contribution_receipt_date": "2025-07-05", "committee_id": "C999", "pdf_url": "u6",
            "committee": {"name": "PAC A", "party_full": "DEM"}
        }
    ]
    
    result = format_cluster_data(data)
    
    # Expect 2 clusters:
    # Cluster 1: Exec A, B, C (Chain works)
    # Cluster 2: Exec D is orphaned (only 1 donor) -> dropped? 
    # Wait, D is May 1. E is Jul 1 (61 days later).
    # So D stands alone. D is 1 person -> Dropped.
    # E and F are Jul 1 and Jul 5 -> Linked. 2 people -> Valid Cluster.
    
    # So expected result: Cluster 1 (A,B,C), Cluster 2 (E,F).
    
    assert len(result) == 2
    
    # Verify Cluster 1
    c1 = next(c for c in result if c['donorCount'] == 3)
    assert len(c1['contributions']) == 3
    assert "Executive Alpha" in [x['donorName'] for x in c1['contributions']]
    assert "Executive Gamma" in [x['donorName'] for x in c1['contributions']]
    
    # Verify Cluster 2
    c2 = next(c for c in result if c['donorCount'] == 2)
    assert len(c2['contributions']) == 2
    assert "Executive Epsilon" in [x['donorName'] for x in c2['contributions']]
    assert "Executive Zeta" in [x['donorName'] for x in c2['contributions']]
    
    # Verify D is missing
    all_donors = []
    for c in result:
        all_donors.extend([x['donorName'] for x in c['contributions']])
    assert "Executive Delta" not in all_donors


def test_format_cluster_data_creates_valid_cluster():
    result = format_cluster_data(SAMPLE_INDIVIDUAL_CONTRIBUTIONS)
    assert len(result) == 1
    cluster = result[0]
    assert cluster['recipientName'] == "A Good Cause PAC"
    assert cluster['donorCount'] == 2
    assert cluster['totalAmount'] == 2500

def test_format_cluster_data_ignores_company_pacs():
    # This is implicitly tested by the above test, which expects only 1 cluster
    # instead of 2.
    result = format_cluster_data(SAMPLE_INDIVIDUAL_CONTRIBUTIONS)
    assert len(result) == 1
    assert not any(c['recipientName'] == 'MSVPAC' for c in result)

def test_format_cluster_data_ignores_single_contributor():
    # Also implicitly tested by the main test
    result = format_cluster_data(SAMPLE_INDIVIDUAL_CONTRIBUTIONS)
    assert not any(c['recipientName'] == 'Future Forward' for c in result)

# --- Tests for format_pac_data --- #

def test_format_pac_data_filters_correctly():
    result = format_pac_data(SAMPLE_PAC_EXPENDITURES)
    assert len(result) == 1
    donation = result[0]
    assert donation['donorName'] == "GOOGLE LLC NETPAC"
    assert donation['recipientName'] == "TROY CARTER FOR CONGRESS"
    assert donation['amount'] == 1000.0

def test_format_pac_data_handles_empty_list():
    assert format_pac_data([]) == []