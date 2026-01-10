erDiagram
    User ||--o{ Fight : creates
    User ||--o{ Tag : creates
    User ||--o{ TagChangeRequest : creates
    
    Country ||--o{ Fighter : "from"
    Country ||--o{ Team : "based_in"
    
    Team ||--o{ Fighter : "member_of"
    
    Fight ||--o{ FightParticipation : "has"
    Fighter ||--o{ FightParticipation : "participates_in"
    
    Fight ||--o{ Tag : "tagged_with"
    Fight ||--o{ TagChangeRequest : "has_pending"
    
    TagType ||--o{ TagChangeRequest : "type_of"
    
    Tag ||--o{ TagChangeRequest : "current_tag"
    
    TagChangeRequest ||--o{ Vote : "receives"

    User {
        uuid id PK
        string username
        string email
        string role "admin, user, system"
        timestamp created_at
        bool isDeleted
    }
    
    Country {
        uuid id PK
        string name
        string code "ISO 3166-1"
        bool isDeleted
    }
    
    Team {
        uuid id PK
        string name
        uuid country_id FK
        timestamp created_at
        bool isDeleted
    }
    
    Fighter {
        uuid id PK
        string name
        uuid country_id FK "nullable"
        uuid team_id FK "nullable"
        timestamp created_at
        bool isDeleted
    }
    
    Fight {
        uuid id PK
        date fight_date
        string location
        uuid created_by FK
        int winner_side "1 or 2, nullable"
        timestamp created_at
        bool isDeleted
        string url
    }
    
    FightParticipation {
        uuid id PK
        uuid fight_id FK
        uuid fighter_id FK "nullable on fighter delete"
        int side "1 or 2"
        string role "fighter, alternate, coach"
        bool isDeleted
    }
    
    TagType {
        uuid id PK
        string name "category, subcategory, weapon, gender, rule_set, custom"
        uuid parent_tag_type_id FK "nullable, for hierarchy"
        bool is_privileged
        int sort_order
        bool isDeleted
    }
    
    Tag {
        uuid id PK
        uuid fight_id FK
        uuid tag_type_id FK
        uuid parent_tag_id FK "nullable, for cascading updates"
        string value "e.g. Singles, Longsword, awesome fight"
        uuid created_by FK
        timestamp created_at
        bool isDeleted
    }
    
    TagChangeRequest {
        uuid id PK
        uuid fight_id FK
        uuid tag_type_id FK
        uuid current_tag_id FK "nullable if adding first tag"
        string proposed_value "e.g. Team, Duel, Rapier"
        int votes_for
        int votes_against
        string status "pending, accepted, rejected, cancelled"
        int threshold "default 10"
        uuid created_by FK
        timestamp created_at
        timestamp resolved_at "nullable"
    }
    
    Vote {
        uuid id PK
        uuid request_id FK
        string session_id "for basic fraud prevention"
        string vote_type "for, against"
        timestamp voted_at
    }