# Chart of accounts — review export

Generated from the versioned JSON packs in `packs/` (data + validator only).
A company chart is composed as **base + exactly one activity + exactly one legal-form layer**; it is never six separate charts.

Generated on 2026-10-11. Pack versions: `base.json` 1.0.0, `contracting.json` 1.0.0, `industrial.json` 1.0.0, `legal_form_joint_stock.json` 1.0.0, `legal_form_sole_proprietorship.json` 1.0.0, `trading.json` 1.0.0.

## صناعية — Industrial · منشأة فردية — Sole proprietorship

_62 accounts._

| Code | Name (AR) | Name (EN) | Type | Postable | System |
| --- | --- | --- | --- | --- | --- |
| `1000` | الأصول | Assets | asset | — | — |
| `1100` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول المتداولة | Current assets | asset | — | — |
| `1110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالصندوق | Cash on hand | asset | yes | — |
| `1120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالبنوك | Cash at bank | asset | yes | — |
| `1130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;العملاء (حساب وسيط) | Customers (control) | asset | yes | yes |
| `1140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أوراق القبض | Notes receivable | asset | yes | — |
| `1150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مدفوعة مقدماً | Prepaid expenses | asset | yes | — |
| `1160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المدخلات | VAT input (recoverable) | asset | yes | yes |
| `1170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - مدينة | Withholding tax receivable | asset | yes | yes |
| `1180` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول غير المتداولة | Non-current assets | asset | — | — |
| `1181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الأصول الثابتة | Property, plant and equipment | asset | yes | — |
| `1182` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مجمع إهلاك الأصول الثابتة | Accumulated depreciation | asset | yes | — |
| `1300` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المخزون | Inventory | asset | — | — |
| `1310` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مخزون المواد الخام | Raw materials inventory | asset | yes | yes |
| `1320` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;إنتاج تحت التشغيل | Work in progress | asset | yes | yes |
| `1330` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مخزون الإنتاج التام | Finished goods inventory | asset | yes | yes |
| `1340` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قطع الغيار | Spare parts inventory | asset | yes | yes |
| `2000` | الالتزامات | Liabilities | liability | — | — |
| `2100` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات المتداولة | Current liabilities | liability | — | — |
| `2110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الموردون (حساب وسيط) | Suppliers (control) | liability | yes | yes |
| `2120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مستحقة | Accrued expenses | liability | yes | — |
| `2130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب مستحقة الدفع | Salaries payable | liability | yes | — |
| `2140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تأمينات اجتماعية مستحقة الدفع | Social insurance payable | liability | yes | — |
| `2150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - دائنة | Withholding tax payable | liability | yes | yes |
| `2160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المخرجات | VAT output (payable) | liability | yes | yes |
| `2170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تسوية ضريبة القيمة المضافة | VAT settlement | liability | yes | yes |
| `2180` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات غير المتداولة | Non-current liabilities | liability | — | — |
| `2181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قروض طويلة الأجل | Long-term loans | liability | yes | — |
| `3000` | حقوق الملكية | Equity | equity | — | — |
| `3100` | &nbsp;&nbsp;&nbsp;&nbsp;رأس مال المالك | Owner's capital | equity | yes | — |
| `3110` | &nbsp;&nbsp;&nbsp;&nbsp;جاري المالك (المسحوبات) | Owner's current account (drawings) | equity | yes | — |
| `3120` | &nbsp;&nbsp;&nbsp;&nbsp;الأرباح المحتجزة | Retained earnings | equity | yes | yes |
| `4000` | الإيرادات | Revenue | revenue | — | — |
| `4200` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات بيع الإنتاج | Revenue from sales of manufactured goods | revenue | yes | — |
| `4210` | &nbsp;&nbsp;&nbsp;&nbsp;مردودات وخصومات المبيعات | Sales returns and discounts | revenue | yes | — |
| `5000` | تكلفة المبيعات والتكاليف المباشرة | Cost of sales and direct costs | expense | — | — |
| `5200` | &nbsp;&nbsp;&nbsp;&nbsp;المواد الخام المستخدمة | Raw materials used | expense | yes | — |
| `5210` | &nbsp;&nbsp;&nbsp;&nbsp;العمالة المباشرة | Direct labor | expense | yes | — |
| `5220` | &nbsp;&nbsp;&nbsp;&nbsp;التكاليف الصناعية غير المباشرة | Manufacturing overhead | expense | yes | — |
| `5230` | &nbsp;&nbsp;&nbsp;&nbsp;تكلفة الإنتاج التام | Cost of goods manufactured | expense | yes | — |
| `5240` | &nbsp;&nbsp;&nbsp;&nbsp;تكلفة المبيعات | Cost of goods sold | expense | yes | — |
| `5250` | &nbsp;&nbsp;&nbsp;&nbsp;الخردة والهالك | Scrap and waste | expense | yes | — |
| `6000` | المصروفات التشغيلية | Operating expenses | expense | — | — |
| `6100` | &nbsp;&nbsp;&nbsp;&nbsp;المصروفات البيعية والتوزيعية | Selling and distribution expenses | expense | — | — |
| `6110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بيعية | Selling expenses | expense | yes | — |
| `6120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات تسويق وإعلان | Marketing and advertising expenses | expense | yes | — |
| `6200` | &nbsp;&nbsp;&nbsp;&nbsp;مصروفات إدارية وعمومية | General and administrative expenses | expense | — | — |
| `6210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب وأجور إدارية | Administrative salaries and wages | expense | yes | — |
| `6220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإيجار | Rent expense | expense | yes | — |
| `6230` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مرافق وخدمات | Utilities expense | expense | yes | — |
| `6240` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإهلاك | Depreciation expense | expense | yes | — |
| `6250` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بنكية وعمولات | Bank charges | expense | yes | — |
| `6260` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أتعاب مهنية وقانونية | Professional and legal fees | expense | yes | — |
| `6270` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مكتبية وعمومية | Office and general expenses | expense | yes | — |
| `7000` | إيرادات أخرى | Other income | revenue | — | — |
| `7110` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - محققة | Foreign exchange gain - realized | revenue | yes | yes |
| `7120` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - غير محققة | Foreign exchange gain - unrealized | revenue | yes | yes |
| `7130` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات أخرى متنوعة | Other miscellaneous income | revenue | yes | — |
| `7500` | مصروفات أخرى | Other expenses | expense | — | — |
| `7610` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - محققة | Foreign exchange loss - realized | expense | yes | yes |
| `7620` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - غير محققة | Foreign exchange loss - unrealized | expense | yes | yes |
| `7630` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات أخرى متنوعة | Other miscellaneous expenses | expense | yes | — |

## صناعية — Industrial · شركة مساهمة — Joint stock

_66 accounts._

| Code | Name (AR) | Name (EN) | Type | Postable | System |
| --- | --- | --- | --- | --- | --- |
| `1000` | الأصول | Assets | asset | — | — |
| `1100` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول المتداولة | Current assets | asset | — | — |
| `1110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالصندوق | Cash on hand | asset | yes | — |
| `1120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالبنوك | Cash at bank | asset | yes | — |
| `1130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;العملاء (حساب وسيط) | Customers (control) | asset | yes | yes |
| `1140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أوراق القبض | Notes receivable | asset | yes | — |
| `1150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مدفوعة مقدماً | Prepaid expenses | asset | yes | — |
| `1160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المدخلات | VAT input (recoverable) | asset | yes | yes |
| `1170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - مدينة | Withholding tax receivable | asset | yes | yes |
| `1180` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول غير المتداولة | Non-current assets | asset | — | — |
| `1181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الأصول الثابتة | Property, plant and equipment | asset | yes | — |
| `1182` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مجمع إهلاك الأصول الثابتة | Accumulated depreciation | asset | yes | — |
| `1300` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المخزون | Inventory | asset | — | — |
| `1310` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مخزون المواد الخام | Raw materials inventory | asset | yes | yes |
| `1320` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;إنتاج تحت التشغيل | Work in progress | asset | yes | yes |
| `1330` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مخزون الإنتاج التام | Finished goods inventory | asset | yes | yes |
| `1340` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قطع الغيار | Spare parts inventory | asset | yes | yes |
| `2000` | الالتزامات | Liabilities | liability | — | — |
| `2100` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات المتداولة | Current liabilities | liability | — | — |
| `2110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الموردون (حساب وسيط) | Suppliers (control) | liability | yes | yes |
| `2120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مستحقة | Accrued expenses | liability | yes | — |
| `2130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب مستحقة الدفع | Salaries payable | liability | yes | — |
| `2140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تأمينات اجتماعية مستحقة الدفع | Social insurance payable | liability | yes | — |
| `2150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - دائنة | Withholding tax payable | liability | yes | yes |
| `2160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المخرجات | VAT output (payable) | liability | yes | yes |
| `2170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تسوية ضريبة القيمة المضافة | VAT settlement | liability | yes | yes |
| `2180` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات غير المتداولة | Non-current liabilities | liability | — | — |
| `2181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قروض طويلة الأجل | Long-term loans | liability | yes | — |
| `3000` | حقوق الملكية | Equity | equity | — | — |
| `3200` | &nbsp;&nbsp;&nbsp;&nbsp;رأس المال المدفوع | Issued share capital | equity | yes | — |
| `3210` | &nbsp;&nbsp;&nbsp;&nbsp;علاوة الإصدار | Share premium | equity | yes | — |
| `3220` | &nbsp;&nbsp;&nbsp;&nbsp;الاحتياطي القانوني | Legal reserve | equity | yes | — |
| `3230` | &nbsp;&nbsp;&nbsp;&nbsp;احتياطيات أخرى | Other reserves | equity | yes | — |
| `3240` | &nbsp;&nbsp;&nbsp;&nbsp;الأرباح المحتجزة | Retained earnings | equity | yes | yes |
| `3250` | &nbsp;&nbsp;&nbsp;&nbsp;جاري المساهمين | Shareholders' current accounts | equity | yes | — |
| `3260` | &nbsp;&nbsp;&nbsp;&nbsp;توزيعات أرباح مستحقة الدفع | Dividends payable | equity | yes | — |
| `4000` | الإيرادات | Revenue | revenue | — | — |
| `4200` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات بيع الإنتاج | Revenue from sales of manufactured goods | revenue | yes | — |
| `4210` | &nbsp;&nbsp;&nbsp;&nbsp;مردودات وخصومات المبيعات | Sales returns and discounts | revenue | yes | — |
| `5000` | تكلفة المبيعات والتكاليف المباشرة | Cost of sales and direct costs | expense | — | — |
| `5200` | &nbsp;&nbsp;&nbsp;&nbsp;المواد الخام المستخدمة | Raw materials used | expense | yes | — |
| `5210` | &nbsp;&nbsp;&nbsp;&nbsp;العمالة المباشرة | Direct labor | expense | yes | — |
| `5220` | &nbsp;&nbsp;&nbsp;&nbsp;التكاليف الصناعية غير المباشرة | Manufacturing overhead | expense | yes | — |
| `5230` | &nbsp;&nbsp;&nbsp;&nbsp;تكلفة الإنتاج التام | Cost of goods manufactured | expense | yes | — |
| `5240` | &nbsp;&nbsp;&nbsp;&nbsp;تكلفة المبيعات | Cost of goods sold | expense | yes | — |
| `5250` | &nbsp;&nbsp;&nbsp;&nbsp;الخردة والهالك | Scrap and waste | expense | yes | — |
| `6000` | المصروفات التشغيلية | Operating expenses | expense | — | — |
| `6100` | &nbsp;&nbsp;&nbsp;&nbsp;المصروفات البيعية والتوزيعية | Selling and distribution expenses | expense | — | — |
| `6110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بيعية | Selling expenses | expense | yes | — |
| `6120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات تسويق وإعلان | Marketing and advertising expenses | expense | yes | — |
| `6200` | &nbsp;&nbsp;&nbsp;&nbsp;مصروفات إدارية وعمومية | General and administrative expenses | expense | — | — |
| `6210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب وأجور إدارية | Administrative salaries and wages | expense | yes | — |
| `6220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإيجار | Rent expense | expense | yes | — |
| `6230` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مرافق وخدمات | Utilities expense | expense | yes | — |
| `6240` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإهلاك | Depreciation expense | expense | yes | — |
| `6250` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بنكية وعمولات | Bank charges | expense | yes | — |
| `6260` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أتعاب مهنية وقانونية | Professional and legal fees | expense | yes | — |
| `6270` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مكتبية وعمومية | Office and general expenses | expense | yes | — |
| `7000` | إيرادات أخرى | Other income | revenue | — | — |
| `7110` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - محققة | Foreign exchange gain - realized | revenue | yes | yes |
| `7120` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - غير محققة | Foreign exchange gain - unrealized | revenue | yes | yes |
| `7130` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات أخرى متنوعة | Other miscellaneous income | revenue | yes | — |
| `7500` | مصروفات أخرى | Other expenses | expense | — | — |
| `7610` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - محققة | Foreign exchange loss - realized | expense | yes | yes |
| `7620` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - غير محققة | Foreign exchange loss - unrealized | expense | yes | yes |
| `7630` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات أخرى متنوعة | Other miscellaneous expenses | expense | yes | — |

## مقاولات — Contracting · منشأة فردية — Sole proprietorship

_63 accounts._

| Code | Name (AR) | Name (EN) | Type | Postable | System |
| --- | --- | --- | --- | --- | --- |
| `1000` | الأصول | Assets | asset | — | — |
| `1100` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول المتداولة | Current assets | asset | — | — |
| `1110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالصندوق | Cash on hand | asset | yes | — |
| `1120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالبنوك | Cash at bank | asset | yes | — |
| `1130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;العملاء (حساب وسيط) | Customers (control) | asset | yes | yes |
| `1140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أوراق القبض | Notes receivable | asset | yes | — |
| `1150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مدفوعة مقدماً | Prepaid expenses | asset | yes | — |
| `1160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المدخلات | VAT input (recoverable) | asset | yes | yes |
| `1170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - مدينة | Withholding tax receivable | asset | yes | yes |
| `1180` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول غير المتداولة | Non-current assets | asset | — | — |
| `1181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الأصول الثابتة | Property, plant and equipment | asset | yes | — |
| `1182` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مجمع إهلاك الأصول الثابتة | Accumulated depreciation | asset | yes | — |
| `1400` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أعمال تحت التنفيذ | Contract work in progress | asset | — | — |
| `1410` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أعمال تحت التنفيذ - غير مفوترة | Work in progress - unbilled | asset | yes | — |
| `1420` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات مقدمة لمقاولي الباطن | Advances to subcontractors | asset | yes | — |
| `1430` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضمانات حسن التنفيذ وكراسة الشروط | Performance guarantees and bid bonds | asset | yes | — |
| `1440` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات محتجزة لدى العملاء | Retentions receivable | asset | yes | yes |
| `2000` | الالتزامات | Liabilities | liability | — | — |
| `2100` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات المتداولة | Current liabilities | liability | — | — |
| `2110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الموردون (حساب وسيط) | Suppliers (control) | liability | yes | yes |
| `2120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مستحقة | Accrued expenses | liability | yes | — |
| `2130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب مستحقة الدفع | Salaries payable | liability | yes | — |
| `2140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تأمينات اجتماعية مستحقة الدفع | Social insurance payable | liability | yes | — |
| `2150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - دائنة | Withholding tax payable | liability | yes | yes |
| `2160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المخرجات | VAT output (payable) | liability | yes | yes |
| `2170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تسوية ضريبة القيمة المضافة | VAT settlement | liability | yes | yes |
| `2180` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات غير المتداولة | Non-current liabilities | liability | — | — |
| `2181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قروض طويلة الأجل | Long-term loans | liability | yes | — |
| `2400` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المستخلصات ودفعات العملاء | Progress billings and customer advances | liability | — | — |
| `2410` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المستخلصات (فواتير الأعمال) | Progress billings (IPCs) | liability | yes | — |
| `2420` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات مقدمة من العملاء | Advances from customers | liability | yes | — |
| `2430` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات محتجزة لمقاولي الباطن | Retentions payable | liability | yes | yes |
| `3000` | حقوق الملكية | Equity | equity | — | — |
| `3100` | &nbsp;&nbsp;&nbsp;&nbsp;رأس مال المالك | Owner's capital | equity | yes | — |
| `3110` | &nbsp;&nbsp;&nbsp;&nbsp;جاري المالك (المسحوبات) | Owner's current account (drawings) | equity | yes | — |
| `3120` | &nbsp;&nbsp;&nbsp;&nbsp;الأرباح المحتجزة | Retained earnings | equity | yes | yes |
| `4000` | الإيرادات | Revenue | revenue | — | — |
| `4300` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات المقاولات | Contract revenue | revenue | yes | — |
| `5000` | تكلفة المبيعات والتكاليف المباشرة | Cost of sales and direct costs | expense | — | — |
| `5300` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف المواد المباشرة | Direct material costs | expense | yes | — |
| `5310` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف العمالة المباشرة | Direct labor costs | expense | yes | — |
| `5320` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف المعدات | Equipment costs | expense | yes | — |
| `5330` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف مقاولي الباطن | Subcontractor costs | expense | yes | — |
| `6000` | المصروفات التشغيلية | Operating expenses | expense | — | — |
| `6100` | &nbsp;&nbsp;&nbsp;&nbsp;المصروفات البيعية والتوزيعية | Selling and distribution expenses | expense | — | — |
| `6110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بيعية | Selling expenses | expense | yes | — |
| `6120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات تسويق وإعلان | Marketing and advertising expenses | expense | yes | — |
| `6200` | &nbsp;&nbsp;&nbsp;&nbsp;مصروفات إدارية وعمومية | General and administrative expenses | expense | — | — |
| `6210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب وأجور إدارية | Administrative salaries and wages | expense | yes | — |
| `6220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإيجار | Rent expense | expense | yes | — |
| `6230` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مرافق وخدمات | Utilities expense | expense | yes | — |
| `6240` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإهلاك | Depreciation expense | expense | yes | — |
| `6250` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بنكية وعمولات | Bank charges | expense | yes | — |
| `6260` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أتعاب مهنية وقانونية | Professional and legal fees | expense | yes | — |
| `6270` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مكتبية وعمومية | Office and general expenses | expense | yes | — |
| `7000` | إيرادات أخرى | Other income | revenue | — | — |
| `7110` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - محققة | Foreign exchange gain - realized | revenue | yes | yes |
| `7120` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - غير محققة | Foreign exchange gain - unrealized | revenue | yes | yes |
| `7130` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات أخرى متنوعة | Other miscellaneous income | revenue | yes | — |
| `7500` | مصروفات أخرى | Other expenses | expense | — | — |
| `7610` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - محققة | Foreign exchange loss - realized | expense | yes | yes |
| `7620` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - غير محققة | Foreign exchange loss - unrealized | expense | yes | yes |
| `7630` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات أخرى متنوعة | Other miscellaneous expenses | expense | yes | — |

## مقاولات — Contracting · شركة مساهمة — Joint stock

_67 accounts._

| Code | Name (AR) | Name (EN) | Type | Postable | System |
| --- | --- | --- | --- | --- | --- |
| `1000` | الأصول | Assets | asset | — | — |
| `1100` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول المتداولة | Current assets | asset | — | — |
| `1110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالصندوق | Cash on hand | asset | yes | — |
| `1120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالبنوك | Cash at bank | asset | yes | — |
| `1130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;العملاء (حساب وسيط) | Customers (control) | asset | yes | yes |
| `1140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أوراق القبض | Notes receivable | asset | yes | — |
| `1150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مدفوعة مقدماً | Prepaid expenses | asset | yes | — |
| `1160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المدخلات | VAT input (recoverable) | asset | yes | yes |
| `1170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - مدينة | Withholding tax receivable | asset | yes | yes |
| `1180` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول غير المتداولة | Non-current assets | asset | — | — |
| `1181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الأصول الثابتة | Property, plant and equipment | asset | yes | — |
| `1182` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مجمع إهلاك الأصول الثابتة | Accumulated depreciation | asset | yes | — |
| `1400` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أعمال تحت التنفيذ | Contract work in progress | asset | — | — |
| `1410` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أعمال تحت التنفيذ - غير مفوترة | Work in progress - unbilled | asset | yes | — |
| `1420` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات مقدمة لمقاولي الباطن | Advances to subcontractors | asset | yes | — |
| `1430` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضمانات حسن التنفيذ وكراسة الشروط | Performance guarantees and bid bonds | asset | yes | — |
| `1440` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات محتجزة لدى العملاء | Retentions receivable | asset | yes | yes |
| `2000` | الالتزامات | Liabilities | liability | — | — |
| `2100` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات المتداولة | Current liabilities | liability | — | — |
| `2110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الموردون (حساب وسيط) | Suppliers (control) | liability | yes | yes |
| `2120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مستحقة | Accrued expenses | liability | yes | — |
| `2130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب مستحقة الدفع | Salaries payable | liability | yes | — |
| `2140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تأمينات اجتماعية مستحقة الدفع | Social insurance payable | liability | yes | — |
| `2150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - دائنة | Withholding tax payable | liability | yes | yes |
| `2160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المخرجات | VAT output (payable) | liability | yes | yes |
| `2170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تسوية ضريبة القيمة المضافة | VAT settlement | liability | yes | yes |
| `2180` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات غير المتداولة | Non-current liabilities | liability | — | — |
| `2181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قروض طويلة الأجل | Long-term loans | liability | yes | — |
| `2400` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المستخلصات ودفعات العملاء | Progress billings and customer advances | liability | — | — |
| `2410` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المستخلصات (فواتير الأعمال) | Progress billings (IPCs) | liability | yes | — |
| `2420` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات مقدمة من العملاء | Advances from customers | liability | yes | — |
| `2430` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;دفعات محتجزة لمقاولي الباطن | Retentions payable | liability | yes | yes |
| `3000` | حقوق الملكية | Equity | equity | — | — |
| `3200` | &nbsp;&nbsp;&nbsp;&nbsp;رأس المال المدفوع | Issued share capital | equity | yes | — |
| `3210` | &nbsp;&nbsp;&nbsp;&nbsp;علاوة الإصدار | Share premium | equity | yes | — |
| `3220` | &nbsp;&nbsp;&nbsp;&nbsp;الاحتياطي القانوني | Legal reserve | equity | yes | — |
| `3230` | &nbsp;&nbsp;&nbsp;&nbsp;احتياطيات أخرى | Other reserves | equity | yes | — |
| `3240` | &nbsp;&nbsp;&nbsp;&nbsp;الأرباح المحتجزة | Retained earnings | equity | yes | yes |
| `3250` | &nbsp;&nbsp;&nbsp;&nbsp;جاري المساهمين | Shareholders' current accounts | equity | yes | — |
| `3260` | &nbsp;&nbsp;&nbsp;&nbsp;توزيعات أرباح مستحقة الدفع | Dividends payable | equity | yes | — |
| `4000` | الإيرادات | Revenue | revenue | — | — |
| `4300` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات المقاولات | Contract revenue | revenue | yes | — |
| `5000` | تكلفة المبيعات والتكاليف المباشرة | Cost of sales and direct costs | expense | — | — |
| `5300` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف المواد المباشرة | Direct material costs | expense | yes | — |
| `5310` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف العمالة المباشرة | Direct labor costs | expense | yes | — |
| `5320` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف المعدات | Equipment costs | expense | yes | — |
| `5330` | &nbsp;&nbsp;&nbsp;&nbsp;تكاليف مقاولي الباطن | Subcontractor costs | expense | yes | — |
| `6000` | المصروفات التشغيلية | Operating expenses | expense | — | — |
| `6100` | &nbsp;&nbsp;&nbsp;&nbsp;المصروفات البيعية والتوزيعية | Selling and distribution expenses | expense | — | — |
| `6110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بيعية | Selling expenses | expense | yes | — |
| `6120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات تسويق وإعلان | Marketing and advertising expenses | expense | yes | — |
| `6200` | &nbsp;&nbsp;&nbsp;&nbsp;مصروفات إدارية وعمومية | General and administrative expenses | expense | — | — |
| `6210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب وأجور إدارية | Administrative salaries and wages | expense | yes | — |
| `6220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإيجار | Rent expense | expense | yes | — |
| `6230` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مرافق وخدمات | Utilities expense | expense | yes | — |
| `6240` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإهلاك | Depreciation expense | expense | yes | — |
| `6250` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بنكية وعمولات | Bank charges | expense | yes | — |
| `6260` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أتعاب مهنية وقانونية | Professional and legal fees | expense | yes | — |
| `6270` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مكتبية وعمومية | Office and general expenses | expense | yes | — |
| `7000` | إيرادات أخرى | Other income | revenue | — | — |
| `7110` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - محققة | Foreign exchange gain - realized | revenue | yes | yes |
| `7120` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - غير محققة | Foreign exchange gain - unrealized | revenue | yes | yes |
| `7130` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات أخرى متنوعة | Other miscellaneous income | revenue | yes | — |
| `7500` | مصروفات أخرى | Other expenses | expense | — | — |
| `7610` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - محققة | Foreign exchange loss - realized | expense | yes | yes |
| `7620` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - غير محققة | Foreign exchange loss - unrealized | expense | yes | yes |
| `7630` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات أخرى متنوعة | Other miscellaneous expenses | expense | yes | — |

## تجارية — Trading · منشأة فردية — Sole proprietorship

_57 accounts._

| Code | Name (AR) | Name (EN) | Type | Postable | System |
| --- | --- | --- | --- | --- | --- |
| `1000` | الأصول | Assets | asset | — | — |
| `1100` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول المتداولة | Current assets | asset | — | — |
| `1110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالصندوق | Cash on hand | asset | yes | — |
| `1120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالبنوك | Cash at bank | asset | yes | — |
| `1130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;العملاء (حساب وسيط) | Customers (control) | asset | yes | yes |
| `1140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أوراق القبض | Notes receivable | asset | yes | — |
| `1150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مدفوعة مقدماً | Prepaid expenses | asset | yes | — |
| `1160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المدخلات | VAT input (recoverable) | asset | yes | yes |
| `1170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - مدينة | Withholding tax receivable | asset | yes | yes |
| `1180` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول غير المتداولة | Non-current assets | asset | — | — |
| `1181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الأصول الثابتة | Property, plant and equipment | asset | yes | — |
| `1182` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مجمع إهلاك الأصول الثابتة | Accumulated depreciation | asset | yes | — |
| `1200` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المخزون | Inventory | asset | — | — |
| `1210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مخزون البضاعة | Merchandise inventory | asset | yes | yes |
| `1220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;بضاعة بالطريق | Goods in transit | asset | yes | — |
| `2000` | الالتزامات | Liabilities | liability | — | — |
| `2100` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات المتداولة | Current liabilities | liability | — | — |
| `2110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الموردون (حساب وسيط) | Suppliers (control) | liability | yes | yes |
| `2120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مستحقة | Accrued expenses | liability | yes | — |
| `2130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب مستحقة الدفع | Salaries payable | liability | yes | — |
| `2140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تأمينات اجتماعية مستحقة الدفع | Social insurance payable | liability | yes | — |
| `2150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - دائنة | Withholding tax payable | liability | yes | yes |
| `2160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المخرجات | VAT output (payable) | liability | yes | yes |
| `2170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تسوية ضريبة القيمة المضافة | VAT settlement | liability | yes | yes |
| `2180` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات غير المتداولة | Non-current liabilities | liability | — | — |
| `2181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قروض طويلة الأجل | Long-term loans | liability | yes | — |
| `3000` | حقوق الملكية | Equity | equity | — | — |
| `3100` | &nbsp;&nbsp;&nbsp;&nbsp;رأس مال المالك | Owner's capital | equity | yes | — |
| `3110` | &nbsp;&nbsp;&nbsp;&nbsp;جاري المالك (المسحوبات) | Owner's current account (drawings) | equity | yes | — |
| `3120` | &nbsp;&nbsp;&nbsp;&nbsp;الأرباح المحتجزة | Retained earnings | equity | yes | yes |
| `4000` | الإيرادات | Revenue | revenue | — | — |
| `4100` | &nbsp;&nbsp;&nbsp;&nbsp;المبيعات | Sales | revenue | yes | — |
| `4110` | &nbsp;&nbsp;&nbsp;&nbsp;مردودات وخصومات المبيعات | Sales returns and discounts | revenue | yes | — |
| `5000` | تكلفة المبيعات والتكاليف المباشرة | Cost of sales and direct costs | expense | — | — |
| `5100` | &nbsp;&nbsp;&nbsp;&nbsp;المشتريات | Purchases | expense | yes | — |
| `5110` | &nbsp;&nbsp;&nbsp;&nbsp;مردودات وخصومات المشتريات | Purchase returns and discounts | expense | yes | — |
| `5120` | &nbsp;&nbsp;&nbsp;&nbsp;تكلفة المبيعات | Cost of goods sold | expense | yes | — |
| `6000` | المصروفات التشغيلية | Operating expenses | expense | — | — |
| `6100` | &nbsp;&nbsp;&nbsp;&nbsp;المصروفات البيعية والتوزيعية | Selling and distribution expenses | expense | — | — |
| `6110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بيعية | Selling expenses | expense | yes | — |
| `6120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات تسويق وإعلان | Marketing and advertising expenses | expense | yes | — |
| `6200` | &nbsp;&nbsp;&nbsp;&nbsp;مصروفات إدارية وعمومية | General and administrative expenses | expense | — | — |
| `6210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب وأجور إدارية | Administrative salaries and wages | expense | yes | — |
| `6220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإيجار | Rent expense | expense | yes | — |
| `6230` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مرافق وخدمات | Utilities expense | expense | yes | — |
| `6240` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإهلاك | Depreciation expense | expense | yes | — |
| `6250` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بنكية وعمولات | Bank charges | expense | yes | — |
| `6260` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أتعاب مهنية وقانونية | Professional and legal fees | expense | yes | — |
| `6270` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مكتبية وعمومية | Office and general expenses | expense | yes | — |
| `7000` | إيرادات أخرى | Other income | revenue | — | — |
| `7110` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - محققة | Foreign exchange gain - realized | revenue | yes | yes |
| `7120` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - غير محققة | Foreign exchange gain - unrealized | revenue | yes | yes |
| `7130` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات أخرى متنوعة | Other miscellaneous income | revenue | yes | — |
| `7500` | مصروفات أخرى | Other expenses | expense | — | — |
| `7610` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - محققة | Foreign exchange loss - realized | expense | yes | yes |
| `7620` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - غير محققة | Foreign exchange loss - unrealized | expense | yes | yes |
| `7630` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات أخرى متنوعة | Other miscellaneous expenses | expense | yes | — |

## تجارية — Trading · شركة مساهمة — Joint stock

_61 accounts._

| Code | Name (AR) | Name (EN) | Type | Postable | System |
| --- | --- | --- | --- | --- | --- |
| `1000` | الأصول | Assets | asset | — | — |
| `1100` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول المتداولة | Current assets | asset | — | — |
| `1110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالصندوق | Cash on hand | asset | yes | — |
| `1120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;النقدية بالبنوك | Cash at bank | asset | yes | — |
| `1130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;العملاء (حساب وسيط) | Customers (control) | asset | yes | yes |
| `1140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أوراق القبض | Notes receivable | asset | yes | — |
| `1150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مدفوعة مقدماً | Prepaid expenses | asset | yes | — |
| `1160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المدخلات | VAT input (recoverable) | asset | yes | yes |
| `1170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - مدينة | Withholding tax receivable | asset | yes | yes |
| `1180` | &nbsp;&nbsp;&nbsp;&nbsp;الأصول غير المتداولة | Non-current assets | asset | — | — |
| `1181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الأصول الثابتة | Property, plant and equipment | asset | yes | — |
| `1182` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مجمع إهلاك الأصول الثابتة | Accumulated depreciation | asset | yes | — |
| `1200` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;المخزون | Inventory | asset | — | — |
| `1210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مخزون البضاعة | Merchandise inventory | asset | yes | yes |
| `1220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;بضاعة بالطريق | Goods in transit | asset | yes | — |
| `2000` | الالتزامات | Liabilities | liability | — | — |
| `2100` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات المتداولة | Current liabilities | liability | — | — |
| `2110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;الموردون (حساب وسيط) | Suppliers (control) | liability | yes | yes |
| `2120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مستحقة | Accrued expenses | liability | yes | — |
| `2130` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب مستحقة الدفع | Salaries payable | liability | yes | — |
| `2140` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تأمينات اجتماعية مستحقة الدفع | Social insurance payable | liability | yes | — |
| `2150` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة الخصم والتحصيل - دائنة | Withholding tax payable | liability | yes | yes |
| `2160` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ضريبة القيمة المضافة - المخرجات | VAT output (payable) | liability | yes | yes |
| `2170` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;تسوية ضريبة القيمة المضافة | VAT settlement | liability | yes | yes |
| `2180` | &nbsp;&nbsp;&nbsp;&nbsp;الالتزامات غير المتداولة | Non-current liabilities | liability | — | — |
| `2181` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;قروض طويلة الأجل | Long-term loans | liability | yes | — |
| `3000` | حقوق الملكية | Equity | equity | — | — |
| `3200` | &nbsp;&nbsp;&nbsp;&nbsp;رأس المال المدفوع | Issued share capital | equity | yes | — |
| `3210` | &nbsp;&nbsp;&nbsp;&nbsp;علاوة الإصدار | Share premium | equity | yes | — |
| `3220` | &nbsp;&nbsp;&nbsp;&nbsp;الاحتياطي القانوني | Legal reserve | equity | yes | — |
| `3230` | &nbsp;&nbsp;&nbsp;&nbsp;احتياطيات أخرى | Other reserves | equity | yes | — |
| `3240` | &nbsp;&nbsp;&nbsp;&nbsp;الأرباح المحتجزة | Retained earnings | equity | yes | yes |
| `3250` | &nbsp;&nbsp;&nbsp;&nbsp;جاري المساهمين | Shareholders' current accounts | equity | yes | — |
| `3260` | &nbsp;&nbsp;&nbsp;&nbsp;توزيعات أرباح مستحقة الدفع | Dividends payable | equity | yes | — |
| `4000` | الإيرادات | Revenue | revenue | — | — |
| `4100` | &nbsp;&nbsp;&nbsp;&nbsp;المبيعات | Sales | revenue | yes | — |
| `4110` | &nbsp;&nbsp;&nbsp;&nbsp;مردودات وخصومات المبيعات | Sales returns and discounts | revenue | yes | — |
| `5000` | تكلفة المبيعات والتكاليف المباشرة | Cost of sales and direct costs | expense | — | — |
| `5100` | &nbsp;&nbsp;&nbsp;&nbsp;المشتريات | Purchases | expense | yes | — |
| `5110` | &nbsp;&nbsp;&nbsp;&nbsp;مردودات وخصومات المشتريات | Purchase returns and discounts | expense | yes | — |
| `5120` | &nbsp;&nbsp;&nbsp;&nbsp;تكلفة المبيعات | Cost of goods sold | expense | yes | — |
| `6000` | المصروفات التشغيلية | Operating expenses | expense | — | — |
| `6100` | &nbsp;&nbsp;&nbsp;&nbsp;المصروفات البيعية والتوزيعية | Selling and distribution expenses | expense | — | — |
| `6110` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بيعية | Selling expenses | expense | yes | — |
| `6120` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات تسويق وإعلان | Marketing and advertising expenses | expense | yes | — |
| `6200` | &nbsp;&nbsp;&nbsp;&nbsp;مصروفات إدارية وعمومية | General and administrative expenses | expense | — | — |
| `6210` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;رواتب وأجور إدارية | Administrative salaries and wages | expense | yes | — |
| `6220` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإيجار | Rent expense | expense | yes | — |
| `6230` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مرافق وخدمات | Utilities expense | expense | yes | — |
| `6240` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروف الإهلاك | Depreciation expense | expense | yes | — |
| `6250` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات بنكية وعمولات | Bank charges | expense | yes | — |
| `6260` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;أتعاب مهنية وقانونية | Professional and legal fees | expense | yes | — |
| `6270` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات مكتبية وعمومية | Office and general expenses | expense | yes | — |
| `7000` | إيرادات أخرى | Other income | revenue | — | — |
| `7110` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - محققة | Foreign exchange gain - realized | revenue | yes | yes |
| `7120` | &nbsp;&nbsp;&nbsp;&nbsp;أرباح فروق العملة - غير محققة | Foreign exchange gain - unrealized | revenue | yes | yes |
| `7130` | &nbsp;&nbsp;&nbsp;&nbsp;إيرادات أخرى متنوعة | Other miscellaneous income | revenue | yes | — |
| `7500` | مصروفات أخرى | Other expenses | expense | — | — |
| `7610` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - محققة | Foreign exchange loss - realized | expense | yes | yes |
| `7620` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;خسائر فروق العملة - غير محققة | Foreign exchange loss - unrealized | expense | yes | yes |
| `7630` | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;مصروفات أخرى متنوعة | Other miscellaneous expenses | expense | yes | — |
