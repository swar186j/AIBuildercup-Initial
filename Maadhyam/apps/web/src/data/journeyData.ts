
export type PassportAssistanceType =
  | "fresh"
  | "reissue"
  | "correction"
  | "documents"
  | "police";

export type AnswerOption = "yes" | "no" | "unsure" | "";

export interface PassportJourneyAnswers {
  assistanceType: PassportAssistanceType;
  applicantAgeGroup: "adult" | "minor" | "";
  currentAddressMatches: AnswerOption;
  hasIdentityDocument: AnswerOption;
  hasAddressDocument: AnswerOption;
  hasDateOfBirthDocument: AnswerOption;
  nameConsistent: AnswerOption;
  policeVerificationStatus:
    | "not-started"
    | "pending"
    | "completed"
    | "delayed"
    | "adverse"
    | "unknown"
    | "";
}

export interface AssistanceOption {
  id: PassportAssistanceType;
  label: string;
  description: string;
}

export const passportAssistanceOptions: AssistanceOption[] = [
  {
    id: "fresh",
    label: "Applying for a new passport",
    description:
      "Prepare for your first passport application.",
  },
  {
    id: "reissue",
    label: "Reissuing an existing passport",
    description:
      "Explore preparation for renewal, expiry or other reissue reasons.",
  },
  {
    id: "correction",
    label: "Correcting personal details",
    description:
      "Review potential differences in name, address or other details.",
  },
  {
    id: "documents",
    label: "Checking document readiness",
    description:
      "Understand which documents may need review.",
  },
  {
    id: "police",
    label: "Getting help with police verification",
    description:
      "Understand verification stages, delays and possible next steps.",
  },
];

export const initialPassportAnswers: PassportJourneyAnswers = {
  assistanceType: "fresh",
  applicantAgeGroup: "",
  currentAddressMatches: "",
  hasIdentityDocument: "",
  hasAddressDocument: "",
  hasDateOfBirthDocument: "",
  nameConsistent: "",
  policeVerificationStatus: "",
};

export const passportJourneySteps = [
  {
    id: "assistance",
    title: "Choose assistance",
    description: "Select what you need help with.",
  },
  {
    id: "context",
    title: "Application context",
    description: "Tell us about your current situation.",
  },
  {
    id: "documents",
    title: "Document preparation",
    description: "Review your available documents.",
  },
  {
    id: "summary",
    title: "Preparation summary",
    description: "Review your answers and next steps.",
  },
] as const;

export type PassportJourneyStep =
  (typeof passportJourneySteps)[number]["id"];

export const passportOfficialUrl =
  "https://www.passportindia.gov.in/";

export const passportJourneyDisclaimer =
  "Maadhyam is an independent assistance platform. This preparation journey does not verify eligibility, confirm document acceptance, determine police verification requirements, or submit an application. Always verify current requirements through official Passport Seva sources.";
