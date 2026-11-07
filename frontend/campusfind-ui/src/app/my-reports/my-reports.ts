import { environment } from '../../environments/environment';

import {
  Component,
  inject,
  OnInit,
  signal
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { ItemService, ItemReport } from '../services/item.service';

@Component({
  selector: 'app-my-reports',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './my-reports.html',
  styleUrl: './my-reports.css'
})
export class MyReports implements OnInit {

  private readonly itemService = inject(ItemService);

  // Reports
  reports = signal<ItemReport[]>([]);
  loading = signal(true);
  errorMessage = signal('');
  deletingId = signal<number | null>(null);
  successMessage = signal('');

  // Edit modal state
  showEditForm = signal(false);
  saving = signal(false);

  // Edit form fields
  editId = signal<number | null>(null);
  editTitle = signal('');
  editDescription = signal('');
  editCategory = signal('Electronics');
  editLocation = signal('');
  editDate = signal('');
  editType = signal<'lost' | 'found'>('lost');

  // Image state
  editSelectedFile = signal<File | null>(null);
  editImagePreview = signal('');

  // Form messages
  editError = signal('');
  editSuccess = signal('');

  readonly reportCategories = [
    'Electronics',
    'Accessories',
    'Documents',
    'Personal Items',
    'Clothing',
    'Books',
    'Others'
  ];

  ngOnInit(): void {
    this.loadMyReports();
  }

  // Load logged-in user's reports
  loadMyReports(): void {
    this.loading.set(true);
    this.errorMessage.set('');

    this.itemService.getMyReports().subscribe({
      next: (data: ItemReport[]) => {
        this.reports.set(data);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load reports:', error);
        this.errorMessage.set(
          error.error?.detail ||
          'Unable to load your reports. Please try again.'
        );
        this.loading.set(false);
      }
    });
  }

  // Convert backend image path into URL
  getImageUrl(imageUrl?: string | null): string {
    if (!imageUrl) {
      return 'https://placehold.co/600x400?text=No+Image';
    }

    if (imageUrl.startsWith('http')) {
      return imageUrl;
    }

    return `${environment.apiUrl}${imageUrl}`;
  }

  // Format report type
  getReportType(type: string): string {
    return type === 'lost' ? 'Lost Item' : 'Found Item';
  }

  // Open edit modal
  openEditForm(report: ItemReport): void {
    this.editId.set(report.id);
    this.editTitle.set(report.title);
    this.editDescription.set(report.description);
    this.editCategory.set(report.category);
    this.editLocation.set(report.location);
    this.editType.set(report.item_type);

    this.editDate.set(
      report.event_date.slice(0, 10)
    );

    this.editImagePreview.set(
      this.getImageUrl(report.image_url)
    );

    this.editSelectedFile.set(null);
    this.editError.set('');
    this.editSuccess.set('');

    this.showEditForm.set(true);
  }

  // Close edit modal
  closeEditForm(): void {
    if (this.saving()) {
      return;
    }

    this.showEditForm.set(false);
    this.resetEditForm();
  }

  // Reset edit form
  resetEditForm(): void {
    this.editId.set(null);
    this.editTitle.set('');
    this.editDescription.set('');
    this.editCategory.set('Electronics');
    this.editLocation.set('');
    this.editDate.set('');
    this.editType.set('lost');

    this.editSelectedFile.set(null);
    this.editImagePreview.set('');

    this.editError.set('');
    this.editSuccess.set('');
  }

  // Select replacement image
  onEditFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    this.editError.set('');

    if (!file) {
      return;
    }

    if (!file.type.startsWith('image/')) {
      this.editError.set('Please select a valid image file.');
      input.value = '';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.editError.set('Image size must be less than 5 MB.');
      input.value = '';
      return;
    }

    this.editSelectedFile.set(file);
    this.editImagePreview.set(URL.createObjectURL(file));
  }

  // Save edited report
  saveEditedReport(): void {
    this.editError.set('');
    this.editSuccess.set('');

    const id = this.editId();

    if (!id) {
      this.editError.set('Invalid report ID.');
      return;
    }

    if (
      !this.editTitle().trim() ||
      !this.editDescription().trim() ||
      !this.editLocation().trim() ||
      !this.editDate()
    ) {
      this.editError.set('Please complete all required fields.');
      return;
    }

    this.saving.set(true);

    const updatedData: Partial<ItemReport> = {
      title: this.editTitle().trim(),
      description: this.editDescription().trim(),
      item_type: this.editType(),
      category: this.editCategory(),
      location: this.editLocation().trim(),
      event_date: `${this.editDate()}T12:00:00`
    };

    // Update report details
    this.itemService.update(id, updatedData).subscribe({
      next: () => {
        const file = this.editSelectedFile();

        // No new image selected
        if (!file) {
          this.finishEdit();
          return;
        }

        // Upload replacement image
        this.itemService.uploadImage(id, file).subscribe({
          next: () => {
            this.finishEdit();
          },
          error: (error) => {
            console.error('Image upload failed:', error);
            this.saving.set(false);
            this.editError.set(
              'Report details were updated, but image upload failed. Please try again.'
            );
            this.loadMyReports();
          }
        });
      },

      error: (error) => {
        console.error('Report update failed:', error);
        this.saving.set(false);
        this.editError.set(
          error.error?.detail ||
          'Unable to update your report. Please try again.'
        );
      }
    });
  }

  // Finish successful update
  finishEdit(): void {
    this.saving.set(false);
    this.editSuccess.set('Your report has been updated successfully!');

    this.loadMyReports();

    setTimeout(() => {
      this.showEditForm.set(false);
      this.resetEditForm();
    }, 1200);
  }

  // Delete report
  deleteReport(item: ItemReport): void {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${item.title}"? This action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    this.deletingId.set(item.id);
    this.errorMessage.set('');
    this.successMessage.set('');

    this.itemService.delete(item.id).subscribe({
      next: () => {
        this.reports.update(currentReports =>
          currentReports.filter(report => report.id !== item.id)
        );

        this.deletingId.set(null);
        this.successMessage.set('Report deleted successfully.');
      },

      error: (error) => {
        console.error('Failed to delete report:', error);
        this.deletingId.set(null);
        this.errorMessage.set(
          error.error?.detail ||
          'Unable to delete this report. Please try again.'
        );
      }
    });
  }

  // Refresh reports
  refreshReports(): void {
    this.successMessage.set('');
    this.loadMyReports();
  }
}

