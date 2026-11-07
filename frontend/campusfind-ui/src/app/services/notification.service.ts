
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Notification {
  id: number;
  user_id: number;
  item_id: number | null;
  claim_id: number | null;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCount {
  unread_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {

  private readonly http = inject(HttpClient);

  private readonly api =
    'http://127.0.0.1:8000/notifications';

  getNotifications(): Observable<Notification[]> {
    return this.http.get<Notification[]>(
      `${this.api}/`
    );
  }

  getUnreadCount(): Observable<UnreadCount> {
    return this.http.get<UnreadCount>(
      `${this.api}/unread-count`
    );
  }

  markAsRead(notificationId: number): Observable<any> {
    return this.http.patch(
      `${this.api}/${notificationId}/read`,
      {}
    );
  }

  markAllAsRead(): Observable<any> {
    return this.http.patch(
      `${this.api}/read-all`,
      {}
    );
  }
}
