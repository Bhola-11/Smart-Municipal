"""
Seed script to populate rich, production-grade municipal demonstration data.
Provides realistic users, departments, wards, categories, SLA policies, and complaints.
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import UserRole
from apps.departments.models import Department
from apps.wards.models import Zone, Ward, Area
from apps.complaints.models import Category, SubCategory, Complaint, ComplaintPriority, ComplaintSeverity, ComplaintStatus
from apps.sla.models import SLAPolicy, SLALog
from apps.assignments.models import Assignment, AssignmentStatus
from apps.workflow.models import WorkflowTransition
from apps.communications.models import ComplaintMessage, MessageType
from apps.feedback.models import Feedback, SatisfactionLevel
from apps.notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with comprehensive, realistic municipal civic data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Commencing CivicFlow database seeding..."))

        # 1. System Administrator
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@civicflow.gov',
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'role': UserRole.ADMIN,
                'designation': 'Principal Civic Commissioner',
                'is_staff': True,
                'is_superuser': True,
                'is_verified_citizen': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"Created Admin: {admin_user.username} (Pass: admin123)"))

        # 2. Zones
        zones_data = [
            ('Central Zone', 'ZONE-C', 'Commercial districts and municipal headquarters'),
            ('North Zone', 'ZONE-N', 'Residential complexes and industrial sectors'),
            ('South Zone', 'ZONE-S', 'Heritage quarters, parks, and university avenue'),
            ('East Zone', 'ZONE-E', 'Suburban layouts and high-density settlements'),
            ('West Zone', 'ZONE-W', 'Information technology corridors and metro routes'),
        ]
        zones = {}
        for name, code, desc in zones_data:
            z, _ = Zone.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
            zones[code] = z

        # 3. Wards & Areas
        wards_data = [
            (1, 'Civic Center Ward', 'ZONE-C', 45000, 'Civic Square, Main Street', [
                ('Town Hall Square', '560001', 'Opposite Municipal HQ', 12.9716, 77.5946),
                ('Market Arcade', '560001', 'Near Central Clocktower', 12.9725, 77.5955),
            ]),
            (2, 'Greenwood Colony', 'ZONE-N', 38000, '4th Cross, Greenwood', [
                ('Lake View Enclave', '560002', 'Near Bellandur Walkway', 12.9800, 77.6000),
                ('Oakridge Boulevard', '560002', 'Beside Community Hospital', 12.9820, 77.6050),
            ]),
            (3, 'Heritage Square', 'ZONE-S', 42000, 'Old Fort Road', [
                ('Museum Road Block', '560003', 'Near Victoria Memorial', 12.9600, 77.5850),
                ('Botanical Gate', '560003', 'West Garden Arch', 12.9620, 77.5890),
            ]),
            (4, 'Riverside Enclave', 'ZONE-E', 51000, 'East Canal Highway', [
                ('Canal Road Locality', '560004', 'Near Sluice Gate 4', 12.9550, 77.6200),
                ('Industrial Phase 1', '560004', 'Adjacent Freight Depot', 12.9580, 77.6250),
            ]),
            (5, 'Cyber Tech Park', 'ZONE-W', 62000, 'Silicon Boulevard', [
                ('Innovation Hub', '560005', 'Near Metro Gate 3', 12.9900, 77.5500),
                ('Residential Sector 7', '560005', 'Behind Tech Tower', 12.9920, 77.5550),
            ]),
        ]
        wards = {}
        areas = {}
        for num, name, zcode, pop, addr, area_list in wards_data:
            w, _ = Ward.objects.get_or_create(
                ward_number=num,
                defaults={
                    'name': name,
                    'zone': zones[zcode],
                    'population': pop,
                    'office_address': addr,
                    'contact_phone': f"080-2200-{num:04d}"
                }
            )
            wards[num] = w
            for aname, pcode, lmark, lat, lng in area_list:
                a, _ = Area.objects.get_or_create(
                    ward=w,
                    name=aname,
                    defaults={'postal_code': pcode, 'landmark': lmark, 'latitude': lat, 'longitude': lng}
                )
                areas[aname] = a

        # 4. Departments
        departments_data = [
            ('Public Works Department', 'PWD', 'Roads, bridges, stormwater drains, public structures', 36),
            ('Solid Waste Management', 'SWM', 'Garbage collection, street sweeping, sanitary disposal', 24),
            ('Water Supply & Sewerage', 'WSS', 'Potable piped water, pipeline leaks, sewer overflows', 24),
            ('Electrical & Street Lighting', 'ESL', 'Street lamps, electrical poles, junction boxes', 18),
            ('Parks & Horticulture', 'HOR', 'Public gardens, roadside tree pruning, park equipment', 48),
            ('Health & Vector Control', 'HVC', 'Mosquito abatement, epidemic prevention, public toilets', 24),
        ]
        departments = {}
        for dname, dcode, desc, sla_h in departments_data:
            dept, _ = Department.objects.get_or_create(
                code=dcode,
                defaults={
                    'name': dname,
                    'description': desc,
                    'default_sla_hours': sla_h,
                    'email': f"{dcode.lower()}@civicflow.gov",
                    'phone': f"080-3300-{dcode}"
                }
            )
            departments[dcode] = dept

        # 5. Managers & Staff Users
        staff_pool = {}
        for dcode, dept in departments.items():
            mgr_username = f"manager_{dcode.lower()}"
            mgr, m_created = User.objects.get_or_create(
                username=mgr_username,
                defaults={
                    'first_name': f"{dcode} Head",
                    'last_name': 'Manager',
                    'email': f"{mgr_username}@civicflow.gov",
                    'role': UserRole.MANAGER,
                    'department': dept,
                    'designation': f"Executive Engineer ({dcode})",
                    'employee_id': f"EMP-{dcode}-001",
                    'is_verified_citizen': True,
                }
            )
            if m_created:
                mgr.set_password('manager123')
                mgr.save()
            dept.head_officer = mgr
            dept.save()

            # 2 Field Officers per department
            staff_pool[dcode] = []
            for i in range(1, 3):
                s_username = f"staff_{dcode.lower()}_{i}"
                st, s_created = User.objects.get_or_create(
                    username=s_username,
                    defaults={
                        'first_name': f"Officer {i}",
                        'last_name': dcode,
                        'email': f"{s_username}@civicflow.gov",
                        'role': UserRole.STAFF,
                        'department': dept,
                        'ward': wards[i],
                        'designation': f"Assistant Field Engineer ({dcode})",
                        'employee_id': f"EMP-{dcode}-{100 + i}",
                    }
                )
                if s_created:
                    st.set_password('staff123')
                    st.save()
                staff_pool[dcode].append(st)

        # 6. Citizens
        citizens_data = [
            ('citizen_john', 'John', 'Doe', 'john.doe@example.com', '+1 555-0101', 1),
            ('citizen_jane', 'Jane', 'Smith', 'jane.smith@example.com', '+1 555-0102', 2),
            ('citizen_rahul', 'Rahul', 'Verma', 'rahul.verma@example.com', '+1 555-0103', 3),
            ('citizen_sarah', 'Sarah', 'Jenkins', 'sarah.jenkins@example.com', '+1 555-0104', 4),
        ]
        citizens = []
        for uname, fname, lname, email, phone, wnum in citizens_data:
            c, c_created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'email': email,
                    'phone_number': phone,
                    'role': UserRole.CITIZEN,
                    'ward': wards[wnum],
                    'is_verified_citizen': True,
                    'address': f"Apartment {wnum}B, Ward {wnum} Colony"
                }
            )
            if c_created:
                c.set_password('citizen123')
                c.save()
            citizens.append(c)

        # 7. Categories & Subcategories
        categories_data = [
            ('Road Damage & Potholes', 'ROAD_DAMAGE', 'PWD', [
                ('Dangerous Deep Pothole', ComplaintPriority.HIGH),
                ('Manhole Cover Missing/Damaged', ComplaintPriority.CRITICAL),
                ('Broken Pavement/Footpath', ComplaintPriority.MEDIUM),
                ('Road Caved In / Sinking', ComplaintPriority.CRITICAL),
            ]),
            ('Street Light & Electricals', 'STREET_LIGHT', 'ESL', [
                ('Street Light Non-functional', ComplaintPriority.MEDIUM),
                ('Exposed Live Wires on Pole', ComplaintPriority.CRITICAL),
                ('Continuous Day Burning', ComplaintPriority.LOW),
                ('Flickering Lamp on High Street', ComplaintPriority.LOW),
            ]),
            ('Solid Waste & Garbage', 'SOLID_WASTE', 'SWM', [
                ('Overflowing Garbage Dumpster', ComplaintPriority.HIGH),
                ('Illegal Waste Dumping in Open Plot', ComplaintPriority.MEDIUM),
                ('Dead Animal Removal', ComplaintPriority.CRITICAL),
                ('Delayed Door-to-Door Pickup', ComplaintPriority.LOW),
            ]),
            ('Water Supply & Quality', 'WATER_SUPPLY', 'WSS', [
                ('Severe Pipeline Burst on Main Road', ComplaintPriority.CRITICAL),
                ('Contaminated / Turbid Tap Water', ComplaintPriority.CRITICAL),
                ('Zero Water Pressure for 48h', ComplaintPriority.HIGH),
                ('Defective Public Standpost', ComplaintPriority.LOW),
            ]),
            ('Drainage & Sewage Spills', 'DRAINAGE', 'PWD', [
                ('Sewage Overflowing onto Street', ComplaintPriority.CRITICAL),
                ('Blocked Stormwater Drain', ComplaintPriority.HIGH),
                ('Stagnant Drain Water & Mosquito Breeding', ComplaintPriority.MEDIUM),
            ]),
            ('Parks & Greenery', 'PARKS', 'HOR', [
                ('Fallen Tree Branch Obstructing Road', ComplaintPriority.HIGH),
                ('Broken Playground Equipment', ComplaintPriority.MEDIUM),
                ('Overgrown Wild Bushes in Park', ComplaintPriority.LOW),
            ]),
        ]
        categories = {}
        for cat_name, cat_code, dept_code, subcats in categories_data:
            cat, _ = Category.objects.get_or_create(
                code=cat_code,
                defaults={
                    'name': cat_name,
                    'default_department': departments[dept_code],
                    'description': f"Civic issues pertaining to {cat_name} handled by {dept_code}"
                }
            )
            categories[cat_code] = cat
            for sub_name, prio in subcats:
                SubCategory.objects.get_or_create(
                    category=cat,
                    name=sub_name,
                    defaults={'default_priority': prio}
                )

        # 8. SLA Policies
        for prio, hrs, resp_hrs in [
            (ComplaintPriority.CRITICAL, 12, 2),
            (ComplaintPriority.HIGH, 24, 4),
            (ComplaintPriority.MEDIUM, 48, 12),
            (ComplaintPriority.LOW, 96, 24),
        ]:
            SLAPolicy.objects.get_or_create(
                name=f"Standard {prio} Policy",
                priority=prio,
                defaults={
                    'resolution_time_hours': hrs,
                    'response_time_hours': resp_hrs,
                    'due_soon_threshold_percent': 75,
                    'is_active': True
                }
            )

        # 9. Realistic Sample Complaints Across Multiple Lifecycle States
        now = timezone.now()
        sample_complaints_specs = [
            (
                "Dangerous deep pothole near school crossing",
                "Large crater measuring 2 feet across in the middle of school road.",
                'ROAD_DAMAGE', ComplaintPriority.HIGH, ComplaintSeverity.SEVERE,
                ComplaintStatus.INVESTIGATION, 1, citizens[0], staff_pool['PWD'][0],
                now - timedelta(hours=14), now + timedelta(hours=10), False
            ),
            (
                "Open manhole cover on central pedestrian boulevard",
                "Manhole lid broken in half, high risk of pedestrian falls at night.",
                'ROAD_DAMAGE', ComplaintPriority.CRITICAL, ComplaintSeverity.HAZARDOUS,
                ComplaintStatus.WORK_IN_PROGRESS, 1, citizens[1], staff_pool['PWD'][0],
                now - timedelta(hours=4), now + timedelta(hours=8), False
            ),
            (
                "Exposed sparking live electric cable near bus stop",
                "Insulation worn out, sparking during rain. Immediate safety hazard.",
                'STREET_LIGHT', ComplaintPriority.CRITICAL, ComplaintSeverity.HAZARDOUS,
                ComplaintStatus.ESCALATED, 2, citizens[2], staff_pool['ESL'][0],
                now - timedelta(hours=28), now - timedelta(hours=16), True
            ),
            (
                "Uncollected commercial garbage rotting in Market Arcade",
                "Dumpster overflowing for 4 days, noxious odor spreading into market.",
                'SOLID_WASTE', ComplaintPriority.HIGH, ComplaintSeverity.SEVERE,
                ComplaintStatus.WORK_IN_PROGRESS, 1, citizens[0], staff_pool['SWM'][0],
                now - timedelta(hours=18), now + timedelta(hours=6), False
            ),
            (
                "Severe main pipeline leak gushing drinking water",
                "Thousands of gallons of drinking water washing down the avenue.",
                'WATER_SUPPLY', ComplaintPriority.HIGH, ComplaintSeverity.SEVERE,
                ComplaintStatus.RESOLVED, 3, citizens[2], staff_pool['WSS'][0],
                now - timedelta(hours=30), now - timedelta(hours=6), False
            ),
            (
                "Sewage overflowing onto pavement outside hospital gate",
                "Blackwater backflow bubbling through manhole, contamination hazard.",
                'DRAINAGE', ComplaintPriority.CRITICAL, ComplaintSeverity.HAZARDOUS,
                ComplaintStatus.CITIZEN_VERIFICATION, 2, citizens[1], staff_pool['PWD'][1],
                now - timedelta(hours=20), now + timedelta(hours=4), False
            ),
            (
                "Broken children's slide with sharp metal edges in park",
                "Slide sheet metal has peeled back; child received cut yesterday.",
                'PARKS', ComplaintPriority.MEDIUM, ComplaintSeverity.MODERATE,
                ComplaintStatus.CLOSED, 3, citizens[3], staff_pool['HOR'][0],
                now - timedelta(days=5), now - timedelta(days=3), False
            ),
            (
                "Street lamps completely dark across entire block",
                "Seven consecutive sodium lamps non-functional for three nights.",
                'STREET_LIGHT', ComplaintPriority.MEDIUM, ComplaintSeverity.MODERATE,
                ComplaintStatus.SUBMITTED, 4, citizens[3], None,
                now - timedelta(hours=2), now + timedelta(hours=46), False
            ),
            (
                "Dead stray animal near residential gate",
                "Deceased animal requires sanitary collection and disposal.",
                'SOLID_WASTE', ComplaintPriority.HIGH, ComplaintSeverity.SEVERE,
                ComplaintStatus.UNDER_REVIEW, 1, citizens[0], None,
                now - timedelta(hours=3), now + timedelta(hours=21), False
            ),
            (
                "Turbid brown water from residential supply taps",
                "Sediment and foul taste reported by entire apartment society.",
                'WATER_SUPPLY', ComplaintPriority.HIGH, ComplaintSeverity.SEVERE,
                ComplaintStatus.REOPENED, 5, citizens[1], staff_pool['WSS'][1],
                now - timedelta(hours=40), now - timedelta(hours=10), True
            ),
        ]

        for title, desc, cat_code, prio, sev, status, wnum, cit, staff, c_time, d_time, is_esc in sample_complaints_specs:
            cat = categories[cat_code]
            sub = cat.subcategories.first()
            ward = wards[wnum]
            area = ward.areas.first()

            complaint, created = Complaint.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'citizen': cit,
                    'category': cat,
                    'subcategory': sub,
                    'department': cat.default_department,
                    'ward': ward,
                    'area': area,
                    'specific_address': f"Near {area.name}, Ward {ward.ward_number}",
                    'priority': prio,
                    'severity': sev,
                    'status': status,
                    'assigned_staff': staff,
                    'expected_resolution_date': d_time,
                    'is_escalated': is_esc,
                    'escalation_level': 1 if is_esc else 0,
                    'reopen_count': 1 if status == ComplaintStatus.REOPENED else 0,
                    'created_at': c_time
                }
            )

            # SLA Record
            sla_status = 'ON_TRACK'
            if status in [ComplaintStatus.RESOLVED, ComplaintStatus.CITIZEN_VERIFICATION, ComplaintStatus.CLOSED]:
                complaint.resolved_at = c_time + timedelta(hours=16)
                if status == ComplaintStatus.CLOSED:
                    complaint.closed_at = complaint.resolved_at + timedelta(hours=24)
                complaint.save()
                sla_status = 'MET_WITHIN_SLA'
            elif d_time < now:
                sla_status = 'BREACHED'
            elif (d_time - now).total_seconds() < 14400:
                sla_status = 'DUE_SOON'

            SLALog.objects.get_or_create(
                complaint=complaint,
                defaults={
                    'start_time': c_time,
                    'deadline': d_time,
                    'status': sla_status,
                    'breached_at': d_time if sla_status == 'BREACHED' else None,
                    'actual_hours_taken': 16.0 if complaint.resolved_at else None
                }
            )

            # Workflow transition record
            WorkflowTransition.objects.get_or_create(
                complaint=complaint,
                from_status='SUBMITTED',
                to_status=status,
                defaults={
                    'actor': staff or admin_user,
                    'notes': f"Docket advanced to {status}.",
                    'reason': 'SystemSeed'
                }
            )

            # Assignment record if assigned
            if staff:
                Assignment.objects.get_or_create(
                    complaint=complaint,
                    staff=staff,
                    defaults={
                        'assigned_by': cat.default_department.head_officer,
                        'reason': 'Assigned by zonal manager based on geographic proximity',
                        'status': AssignmentStatus.ACCEPTED,
                        'accepted_at': c_time + timedelta(hours=1)
                    }
                )

            # Communications message
            ComplaintMessage.objects.get_or_create(
                complaint=complaint,
                sender=cit,
                defaults={
                    'message_type': MessageType.CITIZEN_UPDATE,
                    'message': f"Civic report submitted with high urgency: {title}"
                }
            )

            # Feedback if closed
            if status == ComplaintStatus.CLOSED:
                Feedback.objects.get_or_create(
                    complaint=complaint,
                    defaults={
                        'citizen': cit,
                        'rating': 5,
                        'satisfaction': SatisfactionLevel.VERY_SATISFIED,
                        'resolution_accepted': True,
                        'comments': 'Repairs were prompt and durable. Excellent civic service!'
                    }
                )

        self.stdout.write(self.style.SUCCESS("Municipal data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("Credentials for testing:"))
        self.stdout.write("  Admin:     admin / admin123")
        self.stdout.write("  Managers:  manager_pwd / manager123 (also manager_swm, manager_wss, manager_esl)")
        self.stdout.write("  Staff:     staff_pwd_1 / staff123 (also staff_swm_1, staff_wss_1)")
        self.stdout.write("  Citizens:  citizen_john / citizen123 (also citizen_jane, citizen_rahul)")
