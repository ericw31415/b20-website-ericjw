CREATE TABLE Users (
    username TEXT,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    PRIMARY KEY(username)
);

CREATE TABLE Assessments (
    id INTEGER,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE Marks (
    username TEXT,
    ass_id INTEGER,
    mark INTEGER,
    PRIMARY KEY(username, ass_id),
    FOREIGN KEY(username) REFERENCES Users(username) ON DELETE CASCADE,
    FOREIGN KEY(ass_id) REFERENCES Assessments(id) ON DELETE CASCADE
);

CREATE TABLE Remarks (
    username TEXT,
    ass_id INTEGER,
    why TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY(username, ass_id),
    FOREIGN KEY(username) REFERENCES Users(username) ON DELETE CASCADE,
    FOREIGN KEY(ass_id) REFERENCES Assessments(id) ON DELETE CASCADE
);

CREATE TABLE FeedbackQuestions (
    id INTEGER,
    question TEXT NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE Feedback (
    id INTEGER,
    instructor TEXT NOT NULL,
    q_id INTEGER NOT NULL,
    response TEXT NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(instructor) REFERENCES Users(username) ON DELETE CASCADE,
    FOREIGN KEY(q_id) REFERENCES FeedbackQuestions(id) ON DELETE CASCADE
);
