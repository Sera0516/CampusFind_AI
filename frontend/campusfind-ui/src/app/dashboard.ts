import { environment } from '../environments/environment';

import { DatePipe, UpperCasePipe } from '@angular/common';

import {
  Component,
  computed,
  inject,
  OnInit,
  signal
} from '@angular/core';

import {
  Router,
  RouterLink,
  RouterLinkActive
} from '@angular/router';

import {
  ItemService,
  ItemReport,
  SemanticMatchResponse
} from './services/item.service';

import {
  NotificationService,
  Notification
} from './services/notification.service';

interface CampusItem {
  id: number;
  title: string;
  description: string;
  category: string;
  location: string;
  date: string;
  type: 'Lost' | 'Found';
  image: string;
  status: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    UpperCasePipe,
    DatePipe
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class Dashboard implements OnInit {

  readonly router = inject(Router);

  private readonly itemService = inject(ItemService);
  private readonly notificationService = inject(NotificationService);

  searchTerm = signal('');
  selectedCategory = signal('All');
  selectedType = signal('All');

  loading = signal(true);
  errorMessage = signal('');

  // Notification state
  notifications = signal<Notification[]>([]);
  unreadNotificationCount = signal(0);
  showNotifications = signal(false);
  notificationLoading = signal(false);
  notificationError = signal('');

  // Report form state
  showReportForm = signal(false);
  reportType = signal<'Lost' | 'Found'>('Lost');
  formSubmitting = signal(false);
  formError = signal('');
  formSuccess = signal('');

  // Form fields
  reportTitle = signal('');
  reportDescription = signal('');
  reportCategory = signal('Electronics');
  reportLocation = signal('');
  reportDate = signal(new Date().toISOString().slice(0, 10));

  // Image upload state
  selectedFile = signal<File | null>(null);
  imagePreview = signal('');

  // AI semantic matching state
  selectedMatchItemId = signal<number | null>(null);
  semanticMatchResults = signal<SemanticMatchResponse | null>(null);
  matchingLoading = signal(false);
  matchingError = signal('');

  readonly categories = [
    'All',
    'Electronics',
    'Accessories',
    'Documents',
    'Personal Items'
  ];

  readonly reportCategories = [
    'Electronics',
    'Accessories',
    'Documents',
    'Personal Items',
    'Clothing',
    'Books',
    'Others'
  ];

  readonly items = signal<CampusItem[]>([]);

  ngOnInit(): void {
    this.loadItems();
    this.loadNotifications();
    this.loadUnreadCount();
  }

  // ------------------------------------------
  // Notification functionality
  // ------------------------------------------

  // Load all notifications
  loadNotifications(): void {

    this.notificationLoading.set(true);
    this.notificationError.set('');

    this.notificationService.getNotifications().subscribe({

      next: (response) => {
        this.notifications.set(response);
        this.notificationLoading.set(false);
      },

      error: (error) => {
        console.error('Failed to load notifications:', error);

        this.notificationError.set(
          'Unable to load notifications. Please try again.'
        );

        this.notificationLoading.set(false);
      }
    });
  }

  // Load unread notification count
  loadUnreadCount(): void {

    this.notificationService.getUnreadCount().subscribe({

      next: (response) => {
        this.unreadNotificationCount.set(
          response.unread_count
        );
      },

      error: (error) => {
        console.error('Failed to load unread count:', error);
      }
    });
  }

  // Open or close notification dropdown
  toggleNotifications(): void {

    const isOpening = !this.showNotifications();

    this.showNotifications.set(isOpening);

    if (isOpening) {
      this.loadNotifications();
      this.loadUnreadCount();
    }
  }

  // Mark an individual notification as read
  
markNotificationAsRead(notification: Notification): void {

  const navigateToClaim = (): void => {

    this.showNotifications.set(false);

    if (notification.notification_type === 'new_claim') {

      this.router.navigate(['/received-claims'], {
        queryParams: notification.claim_id
          ? { claimId: notification.claim_id }
          : {}
      });

    } else if (
      notification.notification_type === 'claim_approved' ||
      notification.notification_type === 'claim_rejected'
    ) {

      this.router.navigate(['/my-claims'], {
        queryParams: notification.claim_id
          ? { claimId: notification.claim_id }
          : {}
      });

    }

  };

  // Already read? Navigate directly.
  if (notification.is_read) {
    navigateToClaim();
    return;
  }

  // Mark as read before navigating.
  this.notificationService.markAsRead(notification.id).subscribe({

    next: () => {

      this.notifications.update(current =>
        current.map(item =>
          item.id === notification.id
            ? { ...item, is_read: true }
            : item
        )
      );

      this.loadUnreadCount();

      navigateToClaim();
    },

    error: (error) => {
      console.error('Failed to mark notification as read:', error);
    }

  });
}

  // Mark all notifications as read
  markAllNotificationsAsRead(): void {

    if (this.unreadNotificationCount() === 0) {
      return;
    }

    this.notificationService.markAllAsRead().subscribe({

      next: () => {

        this.notifications.update(current =>
          current.map(item => ({
            ...item,
            is_read: true
          }))
        );

        this.unreadNotificationCount.set(0);
      },

      error: (error) => {
        console.error('Failed to mark all notifications as read:', error);
      }
    });
  }

  // ------------------------------------------
  // Existing item functionality
  // ------------------------------------------

  // Load reports from PostgreSQL
  loadItems(): void {
    this.loading.set(true);
    this.errorMessage.set('');

    this.itemService.getAll().subscribe({
      next: (reports: ItemReport[]) => {

        const mappedItems: CampusItem[] = reports.map(report => ({
          id: report.id,
          title: report.title,
          description: report.description,
          category: report.category,
          location: report.location,

          date: new Date(report.event_date).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
          }),

          type: report.item_type === 'lost' ? 'Lost' : 'Found',

          image: report.image_url
            ? (report.image_url.startsWith('http')
              ? report.image_url
              : `${environment.apiUrl}${report.image_url}`)
            : 'https://placehold.co/700x450?text=No+Image',

          status: report.item_type === 'lost'
            ? 'Recently reported'
            : 'Waiting for owner'
        }));

        this.items.set(mappedItems);
        this.loading.set(false);
      },

      error: (error) => {
        console.error('Failed to load items:', error);

        this.errorMessage.set(
          'Unable to load reports. Please check whether the backend is running.'
        );

        this.loading.set(false);
      }
    });
  }

  // Find or close AI semantic matches for a report
  toggleSemanticMatches(itemId: number): void {

    if (this.selectedMatchItemId() === itemId) {
      this.selectedMatchItemId.set(null);
      this.semanticMatchResults.set(null);
      this.matchingError.set('');
      this.matchingLoading.set(false);
      return;
    }

    this.selectedMatchItemId.set(itemId);
    this.semanticMatchResults.set(null);
    this.matchingError.set('');
    this.matchingLoading.set(true);

    this.itemService.getSemanticMatches(itemId, 10).subscribe({

      next: (response: SemanticMatchResponse) => {

        if (this.selectedMatchItemId() !== itemId) {
          return;
        }

        this.semanticMatchResults.set(response);
        this.matchingLoading.set(false);
      },

      error: (error) => {

        if (this.selectedMatchItemId() !== itemId) {
          return;
        }

        console.error('AI matching failed:', error);

        this.matchingError.set(
          error.error?.detail ||
          'Unable to find potential matches. Please try again.'
        );

        this.matchingLoading.set(false);
      }
    });
  }

  // Open the report form
  openReportForm(type: 'Lost' | 'Found'): void {
    this.reportType.set(type);
    this.resetReportForm();
    this.showReportForm.set(true);
  }

  // Close the report form
  closeReportForm(): void {
    if (this.formSubmitting()) {
      return;
    }

    this.showReportForm.set(false);
    this.resetReportForm();
  }

  // Reset form fields
  resetReportForm(): void {
    this.reportTitle.set('');
    this.reportDescription.set('');
    this.reportCategory.set('Electronics');
    this.reportLocation.set('');
    this.reportDate.set(new Date().toISOString().slice(0, 10));

    this.selectedFile.set(null);
    this.imagePreview.set('');

    this.formError.set('');
    this.formSuccess.set('');
  }

  // Handle image selection
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    this.formError.set('');

    if (!file) {
      return;
    }

    if (!file.type.startsWith('image/')) {
      this.formError.set('Please select a valid image file.');
      input.value = '';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.formError.set('Image size must be less than 5 MB.');
      input.value = '';
      return;
    }

    this.selectedFile.set(file);
    this.imagePreview.set(URL.createObjectURL(file));
  }

  // Submit report to backend
  submitReport(): void {

    this.formError.set('');
    this.formSuccess.set('');

    if (
      !this.reportTitle().trim() ||
      !this.reportDescription().trim() ||
      !this.reportLocation().trim() ||
      !this.reportDate()
    ) {
      this.formError.set('Please complete all required fields.');
      return;
    }

    this.formSubmitting.set(true);

    const reportData: Partial<ItemReport> = {
      title: this.reportTitle().trim(),
      description: this.reportDescription().trim(),
      item_type: this.reportType().toLowerCase() as 'lost' | 'found',
      category: this.reportCategory(),
      location: this.reportLocation().trim(),
      event_date: `${this.reportDate()}T12:00:00`
    };

    this.itemService.create(reportData).subscribe({

      next: (createdReport) => {

        const file = this.selectedFile();

        if (!file) {
          this.finishSubmission();
          return;
        }

        this.itemService.uploadImage(createdReport.id, file).subscribe({

          next: () => {
            this.finishSubmission();
          },

          error: (error) => {
            console.error('Image upload failed:', error);

            this.formSubmitting.set(false);
            this.formError.set(
              'Your report was saved, but the image upload failed. You can try uploading it again later.'
            );

            this.loadItems();
          }
        });
      },

      error: (error) => {
        console.error('Report creation failed:', error);

        this.formSubmitting.set(false);
        this.formError.set(
          error.error?.detail ||
          'Unable to submit your report. Please try again.'
        );
      }
    });
  }

  // Complete successful submission
  finishSubmission(): void {
    this.formSubmitting.set(false);
    this.formSuccess.set('Your report has been submitted successfully!');

    this.loadItems();

    setTimeout(() => {
      this.showReportForm.set(false);
      this.resetReportForm();
    }, 1200);
  }

  // Search and filtering
  filteredItems = computed(() => {

    const term = this.searchTerm().trim().toLowerCase();
    const category = this.selectedCategory();
    const type = this.selectedType();

    return this.items().filter(item => {

      const matchesSearch =
        !term ||
        item.title.toLowerCase().includes(term) ||
        item.description.toLowerCase().includes(term) ||
        item.location.toLowerCase().includes(term);

      const matchesCategory =
        category === 'All' || item.category === category;

      const matchesType =
        type === 'All' || item.type === type;

      return matchesSearch && matchesCategory && matchesType;
    });
  });

  get lostCount(): number {
    return this.items().filter(item => item.type === 'Lost').length;
  }

  get foundCount(): number {
    return this.items().filter(item => item.type === 'Found').length;
  }

  onSearch(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchTerm.set(value);
  }

  setCategory(category: string): void {
    this.selectedCategory.set(category);
  }

  setType(type: string): void {
    this.selectedType.set(type);
  }

  reportItem(type: 'Lost' | 'Found'): void {
    this.openReportForm(type);
  }
}

