/**
 * HIVE LMS Snappy UX & Feedback
 * Vanilla JS logic for all UX enhancements
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. NProgress.js (Assuming CDN is loaded in base.html)
    if (typeof NProgress !== 'undefined') {
        NProgress.configure({ showSpinner: false, trickleSpeed: 200 });

        // Start progress on clicks to other pages
        document.querySelectorAll('a[href]:not([target="_blank"]):not([href^="#"])').forEach(link => {
            link.addEventListener('click', (e) => {
                if (!e.ctrlKey && !e.metaKey && link.hostname === window.location.hostname) {
                    NProgress.start();
                }
            });
        });

        // Start progress on form submissions
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', () => NProgress.start());
        });
    }

    // 2. Skeleton Loaders Removal
    // Simulate loading for 1s to show skeletons if needed, or hide if data is already there
    window.addEventListener('load', () => {
        setTimeout(() => {
            document.querySelectorAll('.skeleton').forEach(el => {
                el.classList.remove('skeleton');
                // Trigger staggered fade-up if child of a list
                if (el.classList.contains('card-item')) {
                    el.style.opacity = '1';
                }
            });
        }, 800);
    });

    // 3. Count Up Animation
    const countUp = (el) => {
        const target = parseFloat(el.innerText);
        const duration = 800; // ms
        const start = 0;
        let startTime = null;

        const animate = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = timestamp - startTime;
            const percentage = Math.min(progress / duration, 1);

            // Easing (outQuad)
            const easeOut = 1 - (1 - percentage) * (1 - percentage);
            const current = (easeOut * target).toFixed(target % 1 === 0 ? 0 : 1);

            el.innerText = current;
            if (percentage < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    };

    document.querySelectorAll('.animate-number').forEach(countUp);

    // 4. CGPA Ring Animation
    const animateRing = () => {
        const ring = document.querySelector('.cgpa-ring-svg circle');
        if (ring) {
            const val = parseFloat(ring.dataset.value || 0);
            const max = parseFloat(ring.dataset.max || 10);
            const radius = ring.r.baseVal.value;
            const circumference = 2 * Math.PI * radius;

            ring.style.strokeDasharray = circumference;
            ring.style.strokeDashoffset = circumference;

            setTimeout(() => {
                const offset = circumference - (val / max) * circumference;
                ring.style.transition = 'stroke-dashoffset 1s ease-out';
                ring.style.strokeDashoffset = offset;
            }, 100);
        }
    };
    animateRing();

    // 5. Toast Notifications
    const createToastContainer = () => {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    };

    const toastContainer = createToastContainer();

    window.showToast = (message, type = 'success') => {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">${message}</div>
            <span class="material-symbols-rounded" style="font-size: 1.2rem; cursor: pointer;" onclick="this.parentElement.remove()">close</span>
        `;
        toastContainer.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Auto dismiss
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    };

    // Global listener for common actions (simulated feedback)
    document.querySelectorAll('form').forEach(form => {
        // Since we reload on submit, we can't easily toast 'after' unless we use session/flash
        // But we can intercept success if it were AJAX. 
        // For now, let's look for flash messages in the DOM and toast them.
    });

    // 6. Keyboard Shortcuts
    let keys = {};
    document.addEventListener('keydown', (e) => {
        keys[e.key.toLowerCase()] = true;

        if (keys['g'] && keys['d']) window.location.href = '/dashboard/student';
        if (keys['g'] && keys['m']) window.location.href = '/dashboard/messages';
        if (keys['g'] && keys['c']) window.location.href = '/dashboard/my-courses';

        if (e.key === '?') toggleShortcuts();
    });

    document.addEventListener('keyup', (e) => {
        keys[e.key.toLowerCase()] = false;
    });

    const toggleShortcuts = () => {
        const modal = document.querySelector('.shortcuts-modal');
        if (modal) modal.classList.toggle('active');
    };

    // 7. Scroll to Top
    const scrollTopBtn = document.createElement('button');
    scrollTopBtn.className = 'scroll-top-btn';
    scrollTopBtn.innerHTML = '<span class="material-symbols-rounded">arrow_upward</span>';
    document.body.appendChild(scrollTopBtn);

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });

    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // 8. Form Improvements (Spinners and Validation)
    document.querySelectorAll('form').forEach(form => {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            form.addEventListener('submit', (e) => {
                // Check if button is already processing
                if (submitBtn.classList.contains('processing')) return;

                const originalHtml = submitBtn.innerHTML;
                const isWide = submitBtn.offsetWidth > 100;

                // Use a tick to ensure browser starts submission before disabling
                setTimeout(() => {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('processing');
                    submitBtn.innerHTML = `<span class="material-symbols-rounded rotate" style="animation: spin 1s linear infinite; font-size: 1.2rem;">progress_activity</span> ${isWide ? 'Processing...' : ''}`;
                }, 0);
            });
        }
    });

    // Inline validation
    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('blur', (e) => {
            // Don't validate if we're clicking the submit button of the same form
            const form = input.closest('form');
            if (form && document.activeElement && form.contains(document.activeElement) && document.activeElement.type === 'submit') {
                return;
            }

            if (input.required && !input.value.trim()) {
                showValidationError(input, 'Required field');
            } else if (input.type === 'email' && input.value && !input.value.includes('@')) {
                showValidationError(input, 'Invalid email format');
            } else {
                clearValidationError(input);
            }
        });

        // Clear error as user types
        input.addEventListener('input', () => {
            if (input.value.trim()) clearValidationError(input);
        });
    });

    function showValidationError(input, msg) {
        input.style.borderColor = 'var(--danger-color)';
        let msgEl = input.parentElement.querySelector('.validation-msg');
        if (!msgEl) {
            msgEl = document.createElement('div');
            msgEl.className = 'validation-msg error';
            input.parentElement.appendChild(msgEl);
        }
        msgEl.innerText = msg;
        msgEl.style.opacity = '1';
        msgEl.style.visibility = 'visible';
        msgEl.style.transform = 'translateY(0)';
    }

    function clearValidationError(input) {
        input.style.borderColor = 'var(--border-color)';
        const msgEl = input.parentElement.querySelector('.validation-msg');
        if (msgEl) {
            msgEl.style.opacity = '0';
            msgEl.style.visibility = 'hidden';
            msgEl.style.transform = 'translateY(-5px)';
        }
    }

    // 9. Lazy Loading Plotly Charts & Caching
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const chartId = container.id;
                const chartData = container.dataset.plotly;

                if (chartId && chartData) {
                    // Caching
                    const cached = sessionStorage.getItem(`chart_${chartId}`);
                    if (cached) {
                        Plotly.newPlot(chartId, JSON.parse(cached).data, JSON.parse(cached).layout);
                    } else {
                        const parsed = JSON.parse(chartData);
                        Plotly.newPlot(chartId, parsed.data, parsed.layout);
                        sessionStorage.setItem(`chart_${chartId}`, chartData);
                    }
                    observer.unobserve(container);
                }
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.plotly-graph-div').forEach(el => observer.observe(el));

    // 10. API Ping & Last Updated Timestamp
    const updateTimeStamps = () => {
        document.querySelectorAll('.last-updated').forEach(el => {
            fetch('/dashboard/student') // Simulated ping since we can't create /api/ping
                .then(response => {
                    if (response.ok) {
                        el.innerText = 'Updated just now';
                    }
                })
                .catch(() => { });
        });
    };

    if (document.querySelector('.last-updated')) {
        setInterval(updateTimeStamps, 60000);
    }

    // 11. Staggered Card Animation
    document.querySelectorAll('.content-wrapper > *').forEach((card, index) => {
        card.style.animationDelay = `${index * 80}ms`;
        card.classList.add('fade-up');
    });

    // 12. Breadcrumbs (Subtle injection if not present)
    const breadcrumbContainer = document.querySelector('.page-title');
    if (breadcrumbContainer && window.location.pathname.includes('/classroom/')) {
        const parts = window.location.pathname.split('/').filter(p => p);
        let breadcrumbs = '';
        let currentPath = '';
        parts.forEach((part, i) => {
            currentPath += '/' + part;
            const label = part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' ');
            breadcrumbs += `${i > 0 ? ' <span style="opacity:0.5; margin:0 5px;">></span> ' : ''}<a href="${currentPath}" style="font-size:0.8rem; color:var(--text-muted);">${label}</a>`;
        });
        const bcEl = document.createElement('div');
        bcEl.innerHTML = breadcrumbs;
        bcEl.style.marginBottom = '2px';
        breadcrumbContainer.prepend(bcEl);
    }
    // Drop Zone Interactions
    document.querySelectorAll('.drop-zone').forEach(zone => {
        ['dragover', 'dragenter'].forEach(evt => {
            zone.addEventListener(evt, (e) => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });
        });

        ['dragleave', 'dragend', 'drop'].forEach(evt => {
            zone.addEventListener(evt, () => {
                zone.classList.remove('drag-over');
            });
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const input = zone.querySelector('input[type="file"]');
                if (input) {
                    input.files = files;
                    showToast(`File "${files[0].name}" ready to upload! ✓`, 'success');
                }
            }
        });
    });
});

// Helper for CSS spin animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .rotate { display: inline-block; }
`;
document.head.appendChild(style);
