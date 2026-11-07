
import {
  Component,
  OnInit,
  inject,
  ChangeDetectorRef
} from '@angular/core';

import { CommonModule, DatePipe } from '@angular/common';
import { Router } from '@angular/router';

import {
  ClaimService,
  Claim
} from '../services/claim.service';

import { ItemService, ItemReport } from '../services/item.service';

interface ClaimWithItem extends Claim {
  item?: ItemReport;
}

@Component({
  selector: 'app-my-claims',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './my-claims.html',
  styleUrl: './my-claims.css'
})
export class MyClaims implements OnInit {

  private readonly claimService = inject(ClaimService);
  private readonly itemService = inject(ItemService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  claims: ClaimWithItem[] = [];

  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    this.loadMyClaims();
  }

  loadMyClaims(): void {
    this.loading = true;
    this.errorMessage = '';

    this.claimService.getMyClaims().subscribe({

      next: (response) => {
        this.claims = response;

        this.claims.forEach((claim) => {
          this.itemService.getById(claim.item_id).subscribe({
            next: (item) => {
              claim.item = item;
              this.cdr.markForCheck();
            },
            error: (error) => {
              console.error(
                `Unable to load item ${claim.item_id}:`,
                error
              );
            }
          });
        });

        this.loading = false;
        this.cdr.markForCheck();
      },

      error: (error) => {
        console.error('Unable to load claims:', error);

        this.errorMessage =
          error.status === 401
            ? 'Please log in to view your claims.'
            : 'Unable to load your claims. Please try again.';

        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  getStatusClass(status: string): string {
    return `status-${status.toLowerCase()}`;
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }

  viewItem(itemId: number): void {
    this.router.navigate(['/item', itemId]);
  }
}
