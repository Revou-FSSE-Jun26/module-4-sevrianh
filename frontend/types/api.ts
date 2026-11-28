// API types. Keys keep the API's snake_case unchanged (FE-25). Timestamps are ISO strings.

export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  created_at: string;
}

export interface Assignee {
  id: string;
  name: string;
  username: string;
}

export interface Card {
  id: string;
  title: string;
  description: string;
  order: number;
  column_id: string;
  assignee_id: string | null;
  assignee: Assignee | null;
  created_by_id: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CardListItem {
  id: string;
  title: string;
  order: number;
  column_id: string;
  column_name: string;
  board_id: string;
  board_name: string;
  assignee_id: string | null;
  assignee: Assignee | null;
}

export interface Comment {
  id: string;
  card_id: string;
  parent_id: string | null;
  author_id: string;
  content: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  type: 'mention';
  message: string;
  is_read: boolean;
  created_at: string;
  comment_id: string;
  card_id: string;
  board_id: string;
}

export interface NotificationPage {
  items: Notification[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  unread_count: number;
}

export interface Board {
  id: string;
  name: string;
  team_id: string;
  created_at: string;
}

export interface Column {
  id: string;
  name: string;
  order: number;
  is_done: boolean;
  cards: Card[];
}

export interface BoardDetail extends Board {
  columns: Column[];
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MoveCardResult {
  card: Card;
  rebalanced: boolean;
}

export interface TeamMember {
  user_id: string;
  name: string;
  username: string;
  role: 'admin' | 'member';
}

export interface AnalyticsData {
  cards_per_column: { column_id: string; column_name: string; count: number }[];
  completed_this_week: number;
  member_activity: { user_id: string; name: string; username: string; event_count: number }[];
  activity_per_day: { date: string; count: number }[];
  start_date: string;
  end_date: string;
}
