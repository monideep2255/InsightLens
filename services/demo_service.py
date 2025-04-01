import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Define sample insights for different company types
DEMO_INSIGHTS = {
    # Technology company insights
    "tech": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This technology company specializes in developing and selling innovative hardware, software, and online services. Their main product categories include consumer electronics (smartphones, computers, wearables), cloud services, and digital content distribution platforms. They primarily target individual consumers and businesses across global markets.</p>
        <p>The company operates in the technology sector with a focus on premium product offerings and a vertically integrated ecosystem that combines hardware, software, and services.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Brand Value + Ecosystem Lock-in</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Powerful Brand Recognition:</strong> Their brand commands premium pricing and strong customer loyalty, allowing them to maintain higher margins than competitors.</li>
            <li><strong>Ecosystem Lock-in:</strong> Their integrated ecosystem of hardware, software, and services creates high switching costs for users who have invested in multiple products within their ecosystem.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our customer satisfaction and loyalty rates remain exceptionally high, with customer retention above 90% in our core markets. This brand loyalty continues to drive repeat purchases across our expanding product lineup."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue Growth:</strong> Annual revenue of $365 billion, representing 8% year-over-year growth</li>
            <li><strong>Profitability:</strong> Operating margin of 30%, among the highest in the industry</li>
            <li><strong>Cash Position:</strong> $195 billion in cash and marketable securities</li>
            <li><strong>Debt Level:</strong> Long-term debt of $110 billion, well-covered by cash reserves</li>
            <li><strong>Capital Allocation:</strong> Aggressive share repurchase program and growing dividend payments</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a disciplined, long-term focused approach to business growth. Key observations:</p>
        <ul>
            <li>Strong emphasis on innovation with substantial R&D investments (8% of revenue)</li>
            <li>Disciplined capital allocation with balanced approach to reinvestment, acquisitions, and shareholder returns</li>
            <li>Clear succession planning with smooth executive transitions</li>
            <li>Compensation structure aligned with long-term performance metrics and shareholder returns</li>
        </ul>
        <p>Management communications are transparent about business challenges while maintaining optimistic but realistic growth projections.</p>
        """
    },
    
    # Financial company insights
    "financial": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This financial institution operates a diversified banking business with four main segments: Consumer Banking, Commercial Banking, Investment Banking, and Wealth Management. The company provides a comprehensive range of financial services including deposit accounts, loans, credit cards, mortgages, investment products, and advisory services.</p>
        <p>Their customer base spans individuals, small businesses, corporations, institutions, and governments across multiple countries, with primary operations concentrated in North America and Europe.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Regulatory + Scale</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Regulatory Barrier:</strong> Banking licenses and regulatory compliance create high barriers to entry, particularly for their investment banking operations.</li>
            <li><strong>Scale Advantages:</strong> Their large customer base and asset size create cost advantages in operations, technology infrastructure, and funding costs.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our deposit base of over $1.2 trillion provides stable, low-cost funding that significantly improves our net interest margin compared to smaller competitors. Additionally, our regulatory technology investments have created compliance capabilities that smaller institutions struggle to match."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $128 billion annual revenue with 6% growth year-over-year</li>
            <li><strong>Net Interest Margin:</strong> 2.8%, improving by 0.2% from previous year</li>
            <li><strong>Efficiency Ratio:</strong> 58%, indicating good cost control</li>
            <li><strong>Capital Ratio:</strong> 13.2% CET1 ratio, well above regulatory requirements</li>
            <li><strong>Return on Assets:</strong> 1.3%, consistent with industry leaders</li>
            <li><strong>Loan Loss Reserves:</strong> Increased to 2.1% of total loan portfolio</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a conservative approach to risk balanced with growth initiatives. Key observations:</p>
        <ul>
            <li>Disciplined risk management with clear credit underwriting standards</li>
            <li>Proactive investment in digital transformation to reduce branch costs while improving customer experience</li>
            <li>Focus on fee-based income streams to reduce reliance on interest rate spreads</li>
            <li>Compensation tied to risk-adjusted performance metrics and regulatory compliance</li>
        </ul>
        <p>Leadership communications emphasize stability and prudent growth rather than aggressive expansion, appropriate for a financial institution of this size.</p>
        """
    },
    
    # Retail company insights
    "retail": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This retail company operates a multi-channel business selling consumer products through physical stores, e-commerce platforms, and marketplace partnerships. Their product categories include groceries, general merchandise, electronics, apparel, and home goods with both private label and national brands.</p>
        <p>The company primarily targets middle-income consumers across North America, with an expanding international presence. They operate approximately 4,800 stores alongside a rapidly growing e-commerce business that now represents 24% of total sales.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Scale + Distribution Network</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Massive Scale:</strong> Their purchasing power and logistics volume create significant cost advantages that enable everyday low pricing while maintaining margins.</li>
            <li><strong>Distribution Network:</strong> Their integrated network of stores, distribution centers, and last-mile delivery infrastructure creates a fulfillment advantage that's difficult to replicate.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our ability to place merchandise within 10 miles of 90% of the U.S. population creates a fulfillment advantage that enables same-day delivery options that few competitors can match at our scale and cost structure."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $615 billion annual revenue with 4.2% growth year-over-year</li>
            <li><strong>Comparable Store Sales:</strong> Increased 3.7% year-over-year</li>
            <li><strong>E-commerce Growth:</strong> 18% year-over-year increase</li>
            <li><strong>Operating Margin:</strong> 4.3%, reflecting the traditionally thin margins of retail</li>
            <li><strong>Inventory Turnover:</strong> 8.5 times annually, improving efficiency</li>
            <li><strong>Free Cash Flow:</strong> $18.5 billion, enabling significant shareholder returns</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a balanced approach to maintaining core retail strength while investing in digital transformation. Key observations:</p>
        <ul>
            <li>Clear focus on omnichannel integration rather than treating stores and e-commerce as separate businesses</li>
            <li>Disciplined capital allocation with emphasis on supply chain modernization</li>
            <li>Increased investment in employee wages and training to reduce turnover</li>
            <li>Data-driven decision making with advanced analytics capabilities</li>
        </ul>
        <p>Management communications are straightforward about competitive challenges from both discount and premium retailers, with specific strategies to address each segment.</p>
        """
    },
    
    # Manufacturing company insights
    "manufacturing": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This manufacturing company designs, produces, and distributes industrial equipment and components for multiple sectors including aerospace, automotive, energy, and construction. Their product portfolio includes specialized machinery, precision components, control systems, and aftermarket parts and services.</p>
        <p>The company primarily serves industrial customers, OEMs, and distributors across global markets, with manufacturing facilities in 12 countries and sales in over 100 markets worldwide.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Intellectual Property + Switching Costs</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Patent Portfolio:</strong> Their extensive patent portfolio (over 3,200 active patents) protects proprietary technology and manufacturing processes that enable superior product performance.</li>
            <li><strong>Switching Costs:</strong> Their components are designed into customer products and production systems, creating high switching costs once integrated into manufacturing processes or product designs.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our customer retention rate exceeds 95% in our core markets, with an average relationship duration of 14 years among our top 100 customers. This stability reflects the mission-critical nature of our components and the significant requalification costs involved in switching suppliers."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $38.5 billion annual revenue with 3.1% growth year-over-year</li>
            <li><strong>Gross Margin:</strong> 34.8%, reflecting premium positioning within industrial segments</li>
            <li><strong>Recurring Revenue:</strong> 42% of sales from aftermarket parts and services</li>
            <li><strong>EBITDA Margin:</strong> 18.5%, consistent with industry leaders</li>
            <li><strong>Return on Invested Capital:</strong> 16.3%, significantly above cost of capital</li>
            <li><strong>Debt-to-EBITDA Ratio:</strong> 1.8x, indicating conservative leverage</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a long-term orientation with focus on sustainable competitive advantages. Key observations:</p>
        <ul>
            <li>Experienced leadership with deep industry expertise and engineering backgrounds</li>
            <li>Significant R&D investment at 6.5% of sales, well above industry average</li>
            <li>Disciplined acquisition strategy focusing on technology capabilities and adjacent markets</li>
            <li>Emphasis on operational excellence with continuous improvement methodologies</li>
        </ul>
        <p>Leadership communications highlight both cyclical industry challenges and structural growth drivers, with clear strategies to manage both aspects of their business environment.</p>
        """
    }
}

# Magnificent 7 specific demo insights
MAGNIFICENT_7_INSIGHTS = {
    "0000320193": {  # Apple
        "business_summary": """
        <h3>Business Summary</h3>
        <p>Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, iPad, Mac, Apple Watch, and AirPods product lines. Apple's key business segments include iPhone, Mac, iPad, Wearables/Home/Accessories, and Services, with the Services segment (including the App Store, iCloud, Apple Music, Apple TV+, Apple Pay) growing in strategic importance.</p>
        <p>Apple products are sold through their retail stores, online stores, direct sales force, third-party cellular network carriers, wholesalers, retailers, and resellers. The company operates globally with the Americas, Europe, and Greater China being its largest markets.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Brand Power + Ecosystem Lock-in</h4>
        <p>Apple has established multiple competitive advantages:</p>
        <ul>
            <li><strong>Powerful Brand and Premium Positioning:</strong> Apple's brand commands premium pricing, enabling higher margins than competitors.</li>
            <li><strong>Integrated Ecosystem:</strong> The company's tightly integrated hardware/software/services ecosystem creates high switching costs for users invested in the Apple environment.</li>
            <li><strong>Design and User Experience:</strong> Consistently praised for hardware design and intuitive interfaces, creating customer loyalty.</li>
            <li><strong>Customer Retention:</strong> Estimated iPhone retention rates above 90% in mature markets.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"We believe the strength of our ecosystem is an enormous differentiator for us, making it significantly easier to introduce new products into the market, and we have made that ecosystem much stronger in recent years with the addition of services that our customers love."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $394.33 billion in fiscal 2023, a slight decrease from previous year</li>
            <li><strong>Gross Margin:</strong> 44.1%, reflecting premium product positioning</li>
            <li><strong>Services Revenue:</strong> $85.2 billion (growing at double-digit rates)</li>
            <li><strong>Cash Position:</strong> $162.1 billion in cash and marketable securities</li>
            <li><strong>Debt:</strong> $111.1 billion, manageable given strong cash position</li>
            <li><strong>Capital Return:</strong> Strong dividend and share repurchase program ($110+ billion returned to shareholders annually)</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Apple's management team under CEO Tim Cook demonstrates disciplined operational expertise with a long-term strategic focus. Key observations:</p>
        <ul>
            <li>Successfully navigated the post-Steve Jobs transition while maintaining innovation pace</li>
            <li>Strong capital allocation discipline with balanced approach to R&D investment, acquisitions, and shareholder returns</li>
            <li>Commitment to privacy and security as core product values, differentiating from competitors</li>
            <li>Expanding services business shows strategic diversification beyond hardware</li>
            <li>Environmental sustainability initiatives integrated into product design and manufacturing</li>
        </ul>
        <p>Management communications are measured and typically conservative with financial projections, with actual results often exceeding guidance.</p>
        """
    },
    "0000789019": {  # Microsoft
        "business_summary": """
        <h3>Business Summary</h3>
        <p>Microsoft Corporation develops, licenses, and sells software services, devices, and solutions worldwide. The company operates through three business segments: Productivity and Business Processes (Office 365, Dynamics), Intelligent Cloud (Azure, server products), and More Personal Computing (Windows, Surface, Xbox).</p>
        <p>Microsoft's Azure cloud platform and Microsoft 365 suite have become core pillars of the company's business model, driving its transformation from traditional software licensing to subscription and cloud services. The company serves individuals, businesses of all sizes, governmental institutions, and educational establishments globally.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Enterprise Lock-in + Network Effects</h4>
        <p>Microsoft has established several durable competitive advantages:</p>
        <ul>
            <li><strong>Enterprise Integration:</strong> Deep integration of Microsoft products within enterprise technology stacks creates significant switching costs.</li>
            <li><strong>Cloud Infrastructure:</strong> Azure's scale and enterprise relationships establish a strong position in the growing cloud market.</li>
            <li><strong>Developer Ecosystem:</strong> Extensive developer tools and GitHub acquisition strengthen developer relationships.</li>
            <li><strong>Business Applications:</strong> Microsoft 365 and Dynamics create workflow lock-in and data integration benefits.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"With Microsoft 365, we have essentially gone from selling individual tools to selling a connected set of experiences across work, school, and home. This comprehensive approach is driving increased usage and higher customer satisfaction."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $211.9 billion in fiscal 2023, with double-digit growth</li>
            <li><strong>Cloud Revenue Growth:</strong> Azure growing at 30%+ year-over-year</li>
            <li><strong>Operating Margin:</strong> 41%, among the highest in large tech companies</li>
            <li><strong>Cash Position:</strong> $111.3 billion in cash and short-term investments</li>
            <li><strong>Debt:</strong> $73.9 billion, well-covered by cash reserves</li>
            <li><strong>Capital Return:</strong> Consistent dividend growth and share repurchases</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Under CEO Satya Nadella's leadership, Microsoft has undergone a significant transformation. Key management strengths include:</p>
        <ul>
            <li>Successful transition from legacy software to cloud and subscription models</li>
            <li>Strategic acquisitions (LinkedIn, GitHub, Activision Blizzard) that expand ecosystem and capabilities</li>
            <li>Culture shift to collaboration-focused growth mindset</li>
            <li>Clear AI strategy with integration across product portfolio</li>
            <li>Balanced investment in current products and emerging technologies</li>
        </ul>
        <p>Management communication is transparent about strategic priorities and challenges, with consistent execution against stated plans.</p>
        """
    },
    "0001018724": {  # Amazon
        "business_summary": """
        <h3>Business Summary</h3>
        <p>Amazon.com, Inc. operates as a multinational technology and e-commerce company. The company's business segments include North America and International retail operations, Amazon Web Services (AWS) for cloud computing, and a growing advertising business.</p>
        <p>Amazon's online marketplace offers hundreds of millions of products across dozens of categories. The company also produces consumer electronics (Echo, Kindle, Fire TV), operates physical stores (including Whole Foods Market), provides streaming services (Prime Video, Music), and offers the industry-leading AWS cloud computing platform.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Scale Economies + Network Effects</h4>
        <p>Amazon has established multiple reinforcing competitive advantages:</p>
        <ul>
            <li><strong>Logistics Network:</strong> Massive fulfillment infrastructure enables fast delivery speeds that competitors struggle to match.</li>
            <li><strong>Marketplace Network Effects:</strong> Over 2 million third-party sellers create a selection advantage that attracts more customers.</li>
            <li><strong>Prime Membership:</strong> Subscription program creates loyalty and increased purchase frequency.</li>
            <li><strong>Cloud Leadership:</strong> AWS's first-mover advantage and scale in cloud computing generates high-margin revenue.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our ability to deliver products to customers in one or two days through our global fulfillment network creates a service level that would be extremely capital intensive for competitors to replicate, and our flywheel economics improve as we scale this network."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $574.8 billion in fiscal 2023, growing 12% year-over-year</li>
            <li><strong>AWS Revenue:</strong> $90.8 billion (16% of total), growing at 13%</li>
            <li><strong>Operating Income:</strong> $36.9 billion, with AWS generating most of the profit</li>
            <li><strong>Cash Flow:</strong> $54.2 billion operating cash flow</li>
            <li><strong>Cash Position:</strong> $86.5 billion in cash and short-term investments</li>
            <li><strong>Capital Expenditures:</strong> $48.4 billion, reflecting continued heavy investment</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Amazon's management under CEO Andy Jassy (former AWS head) continues the company's long-term focus with some adjustments. Key observations:</p>
        <ul>
            <li>Maintaining the customer-centric philosophy established by founder Jeff Bezos</li>
            <li>Increased focus on operational efficiency and profitability following pandemic expansion</li>
            <li>Disciplined capital allocation despite heavy investments in fulfillment and AWS</li>
            <li>Strong culture of innovation with successful expansion into new markets</li>
            <li>Greater emphasis on profitability and cost control in recent quarters</li>
        </ul>
        <p>Management communications highlight both near-term efficiency improvements and continued long-term investments, balancing profitability with growth opportunities.</p>
        """
    },
    "0001652044": {  # Alphabet/Google
        "business_summary": """
        <h3>Business Summary</h3>
        <p>Alphabet Inc. (Google) operates as a technology conglomerate focused on internet-related services and products. The company's core business segments include Google Services (Search, YouTube, Android, Gmail, Maps, Play Store, advertising), Google Cloud, and Other Bets (early-stage technologies).</p>
        <p>Google's advertising revenue remains the primary business driver, derived from its dominant search engine and YouTube platform. The company's Android operating system powers over 70% of global smartphones, while Google Cloud has grown to become a significant cloud computing provider behind AWS and Microsoft Azure.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Data Advantage + Network Effects</h4>
        <p>Alphabet/Google has established several powerful competitive advantages:</p>
        <ul>
            <li><strong>Search Dominance:</strong> ~90% global search market share creates a data advantage that improves search quality.</li>
            <li><strong>Digital Advertising Ecosystem:</strong> Comprehensive ad platforms across search, display, and video create advertiser lock-in.</li>
            <li><strong>Android Platform:</strong> Mobile OS with 70%+ global market share ensures Google services distribution.</li>
            <li><strong>AI/Machine Learning:</strong> Early and substantial AI investments create advantages across product portfolio.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our continued investment in AI is allowing us to deliver more helpful services to users and create more valuable advertising products for businesses. As search becomes more conversational and visual, we're investing in AI to enhance our capabilities in these domains."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $307.4 billion in fiscal 2023, growing 10% year-over-year</li>
            <li><strong>Advertising Revenue:</strong> $237.9 billion (77% of total)</li>
            <li><strong>Google Cloud Revenue:</strong> $33.1 billion, growing at 24%</li>
            <li><strong>Operating Margin:</strong> 27%, reflecting high profitability despite significant R&D</li>
            <li><strong>Cash Position:</strong> $110.9 billion in cash and marketable securities</li>
            <li><strong>Share Repurchases:</strong> $62 billion in 2023, reflecting shareholder return focus</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Under CEO Sundar Pichai, Alphabet has maintained innovation while increasing operational discipline. Key observations:</p>
        <ul>
            <li>Stronger focus on efficiency and cost management in recent years</li>
            <li>Significant investment in AI across the product portfolio</li>
            <li>Balancing short-term profitability with long-term moonshot investments</li>
            <li>Navigating increased regulatory scrutiny in multiple jurisdictions</li>
            <li>Improving capital allocation with more substantial share repurchases</li>
        </ul>
        <p>Management communication has become more detailed regarding cost control and operational efficiency while maintaining the company's innovation-focused culture.</p>
        """
    },
    "0001326801": {  # Meta/Facebook
        "business_summary": """
        <h3>Business Summary</h3>
        <p>Meta Platforms, Inc. (formerly Facebook) develops and operates social media applications and technologies. The company's core platforms include Facebook, Instagram, WhatsApp, and Messenger, which collectively reach billions of users globally. Meta also invests heavily in metaverse technologies through its Reality Labs division.</p>
        <p>The company's primary revenue source is digital advertising across its family of apps, leveraging detailed user data to provide targeted advertising solutions. Meta's business model relies on user engagement and time spent on its platforms to generate advertising inventory.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Network Effects + Scale</h4>
        <p>Meta has established several durable competitive advantages:</p>
        <ul>
            <li><strong>Network Effects:</strong> 3.2+ billion daily active people across Meta's family of apps create powerful network effects.</li>
            <li><strong>Advertising Platform:</strong> Extensive targeting capabilities and measurement tools create advertiser dependency.</li>
            <li><strong>Complementary Apps:</strong> Portfolio of social/messaging apps (Facebook, Instagram, WhatsApp) creates an ecosystem.</li>
            <li><strong>Data Advantage:</strong> Massive user data set enables advertising effectiveness and product improvements.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our competitive advantage is the breadth and depth of our advertising platform that lets businesses of all sizes effectively reach their customers across our family of apps. The precision of our targeting combined with our massive reach creates a unique value proposition."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $134.9 billion in fiscal 2023, growing 16% year-over-year</li>
            <li><strong>Advertising Revenue:</strong> $131.9 billion (98% of total)</li>
            <li><strong>Reality Labs Losses:</strong> $16.1 billion operating loss from metaverse investments</li>
            <li><strong>Operating Margin:</strong> 29%, recovering after efficiency initiatives</li>
            <li><strong>Cash Position:</strong> $61.1 billion in cash and marketable securities</li>
            <li><strong>Share Repurchases:</strong> $20+ billion annually, significant shareholder returns</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Under CEO Mark Zuckerberg, Meta has shown both strategic vision and operational adjustments. Key observations:</p>
        <ul>
            <li>Demonstrated ability to adapt to market changes (mobile shift, Stories format)</li>
            <li>Significant long-term bet on metaverse technologies despite investor skepticism</li>
            <li>2022-2023 "Year of Efficiency" showed responsiveness to profitability concerns</li>
            <li>Successful navigation of multiple competitive threats (TikTok challenge with Reels)</li>
            <li>Handling of content moderation and privacy issues remains challenging</li>
        </ul>
        <p>Management communication has become more transparent about investment timeframes and efficiency measures while maintaining conviction in long-term metaverse vision.</p>
        """
    },
    "0001318605": {  # Tesla
        "business_summary": """
        <h3>Business Summary</h3>
        <p>Tesla, Inc. designs, manufactures, and sells electric vehicles, energy generation systems, and storage products. The company's automotive segment includes Model S, Model 3, Model X, Model Y, and the Cybertruck. Tesla also produces solar panels, solar roof tiles, and battery storage systems through its energy generation and storage segment.</p>
        <p>Tesla maintains a direct-to-consumer sales model through company-owned stores and online, bypassing traditional dealerships in most markets. The company operates manufacturing facilities in the US, China, Germany, and continues to expand production capacity globally.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: First-Mover + Technology Leadership</h4>
        <p>Tesla has established several competitive advantages:</p>
        <ul>
            <li><strong>Vertical Integration:</strong> In-house design and manufacturing of key components, including batteries and chips.</li>
            <li><strong>Software Expertise:</strong> Over-the-air updates and autonomous driving capabilities create ongoing differentiation.</li>
            <li><strong>Supercharger Network:</strong> Extensive global fast-charging infrastructure enhances the ownership experience.</li>
            <li><strong>Brand Strength:</strong> Strong brand enables selling vehicles without traditional advertising.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our vertical integration and software-first approach allow us to rapidly deploy new features and improvements that our customers value. The pace of our innovation creates a moving target for competitors trying to catch up with where we were, not where we're going."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $96.8 billion in fiscal 2023, growing 19% year-over-year</li>
            <li><strong>Automotive Revenue:</strong> $88.2 billion (91% of total)</li>
            <li><strong>Energy Generation/Storage:</strong> $6.0 billion (growing 75% year-over-year)</li>
            <li><strong>Operating Margin:</strong> 9.2%, declining due to price reductions</li>
            <li><strong>Cash Position:</strong> $29.1 billion in cash and marketable securities</li>
            <li><strong>Free Cash Flow:</strong> $4.4 billion, declining from previous year</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Under CEO Elon Musk, Tesla demonstrates high ambition but operational volatility. Key observations:</p>
        <ul>
            <li>Visionary leadership with extremely ambitious goals (autonomous driving, robotics)</li>
            <li>Successful execution in creating a mass-market electric vehicle company despite skepticism</li>
            <li>Manufacturing innovation focused on production efficiency and scalability</li>
            <li>CEO division of attention across multiple companies (SpaceX, X/Twitter) creates management concerns</li>
            <li>Communications often contain ambitious timelines that experience significant delays</li>
        </ul>
        <p>Management communication tends to focus on long-term technological vision rather than near-term financial performance, creating tension with investors focused on quarterly results.</p>
        """
    },
    "0000885639": {  # NVIDIA
        "business_summary": """
        <h3>Business Summary</h3>
        <p>NVIDIA Corporation designs and manufactures computer graphics processors, chipsets, and related multimedia software. The company's business segments include Gaming, Data Center, Professional Visualization, and Automotive. NVIDIA has evolved from primarily a gaming graphics company to a leader in AI and accelerated computing.</p>
        <p>NVIDIA's GPUs have become essential components for AI model training and inference, cloud computing, professional visualization, and high-performance computing applications. The company's software platforms, including CUDA and various AI frameworks, enhance the value of its hardware offerings.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Technology Leadership + Ecosystem Effects</h4>
        <p>NVIDIA has established several powerful competitive advantages:</p>
        <ul>
            <li><strong>GPU Architecture Leadership:</strong> Continuous innovation in graphics and parallel computing architecture.</li>
            <li><strong>CUDA Software Ecosystem:</strong> Proprietary parallel computing platform with extensive developer adoption.</li>
            <li><strong>AI Acceleration:</strong> First-mover advantage in AI computing with purpose-built hardware and software.</li>
            <li><strong>Full-Stack Approach:</strong> Integration of hardware, software, and development frameworks create customer lock-in.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"NVIDIA's computing platform is experiencing rapid adoption because we uniquely provide a combination of full-stack expertise, specialized silicon architecture, and a rich software ecosystem. This integrated approach allows us to solve the most complex computing challenges for our customers."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $60.9 billion in fiscal 2024, growing 126% year-over-year</li>
            <li><strong>Data Center Revenue:</strong> $47.5 billion (78% of total), growing 217%</li>
            <li><strong>Gross Margin:</strong> 72.7%, reflecting high-value products and technology leadership</li>
            <li><strong>Operating Margin:</strong> 53.6%, exceptional profitability</li>
            <li><strong>Cash Position:</strong> $26.9 billion in cash and marketable securities</li>
            <li><strong>Free Cash Flow:</strong> $27.4 billion, generating substantial cash from operations</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>Under founder and CEO Jensen Huang, NVIDIA demonstrates clear strategic vision. Key observations:</p>
        <ul>
            <li>Successful transformation from gaming company to AI and accelerated computing leader</li>
            <li>Long-term investment in GPU computing capabilities predating the AI boom</li>
            <li>Strong ecosystem development through partnerships and developer relations</li>
            <li>Clear strategic communications about company direction and technology roadmap</li>
            <li>Balanced approach to organic growth with targeted acquisitions (Mellanox, Arm attempt)</li>
        </ul>
        <p>Management demonstrates technical depth and clear articulation of complex technology trends, building investor confidence in the company's ability to maintain leadership in rapidly evolving markets.</p>
        """
    }
}

def generate_demo_insights(document_id, company_type="tech"):
    """
    Generate demo insights without making API calls
    
    Args:
        document_id: The ID of the document
        company_type: The type of company to generate insights for (tech, financial, retail, manufacturing)
            Or can be a CIK number for one of the Magnificent 7 companies
    
    Returns:
        dict: A dictionary of insights by category
    """
    # Log that we're using demo mode
    logger.info(f"Generating demo insights for document {document_id}")
    
    # First, check if we have a specific template for this company (Magnificent 7)
    from models import Document
    document = Document.query.get(document_id)
    
    # If we have a CIK and it matches one of the Magnificent 7
    if document and document.cik and document.cik in MAGNIFICENT_7_INSIGHTS:
        logger.info(f"Using Magnificent 7 template for {document.cik} ({document.company_name})")
        return MAGNIFICENT_7_INSIGHTS[document.cik]
    
    # Otherwise fallback to the regular templates
    logger.info(f"Using generic {company_type} template")
    template = DEMO_INSIGHTS.get(company_type.lower(), DEMO_INSIGHTS["tech"])
    
    # Return the insights
    return template


def perform_local_analysis(content):
    """
    Perform rule-based local analysis without using AI APIs
    
    This uses simple text pattern matching to extract insights from the document
    
    Args:
        content: The document content to analyze
        
    Returns:
        dict: A dictionary of insights by category
    """
    logger.info("Performing local rule-based analysis without AI APIs")
    
    # Convert to lowercase for easier pattern matching
    content_lower = content.lower()
    
    # Initialize insights dictionary
    insights = {
        "business_summary": "<h3>Business Summary</h3>",
        "moat": "<h3>Competitive Advantages</h3>",
        "financial": "<h3>Financial Health</h3>",
        "management": "<h3>Management Assessment</h3>"
    }
    
    # --- Business Summary Analysis ---
    business_desc = "<p>Based on document analysis, this company "
    
    # Check for business type indicators
    if any(word in content_lower for word in ["software", "hardware", "technology", "digital", "app", "platform"]):
        business_desc += "appears to operate in the technology sector, "
        if "software" in content_lower:
            business_desc += "developing software products"
        elif "hardware" in content_lower:
            business_desc += "producing hardware devices"
        else:
            business_desc += "providing technology solutions"
    elif any(word in content_lower for word in ["bank", "loan", "deposit", "financial", "investment", "insurance"]):
        business_desc += "operates in the financial services industry, "
        if "bank" in content_lower:
            business_desc += "offering banking services"
        elif "insurance" in content_lower:
            business_desc += "providing insurance products"
        else:
            business_desc += "delivering financial services"
    elif any(word in content_lower for word in ["retail", "store", "shop", "merchandise", "consumer", "product"]):
        business_desc += "is in the retail sector, "
        business_desc += "selling consumer products"
    elif any(word in content_lower for word in ["manufacture", "production", "factory", "industrial", "equipment"]):
        business_desc += "is involved in manufacturing, "
        business_desc += "producing industrial goods"
    else:
        business_desc += "operates across multiple sectors"
    
    business_desc += ".</p>"
    
    # Add customer information if found
    if "customer" in content_lower or "client" in content_lower:
        business_desc += "<p>The company serves "
        if any(word in content_lower for word in ["consumer", "individual", "retail customer"]):
            business_desc += "individual consumers"
        elif any(word in content_lower for word in ["business", "enterprise", "corporate", "company"]):
            business_desc += "business clients"
        elif any(word in content_lower for word in ["government", "public sector"]):
            business_desc += "government entities"
        else:
            business_desc += "various customer segments"
        business_desc += ".</p>"
    
    insights["business_summary"] += business_desc
    
    # --- Moat Analysis ---
    moat_desc = "<p>Potential competitive advantages identified in the document:</p><ul>"
    
    # Check for different types of moats
    moats_found = False
    
    # Brand
    if any(word in content_lower for word in ["brand", "reputation", "recognition", "loyalty"]):
        moat_desc += "<li><strong>Brand Advantage:</strong> The company appears to have brand recognition or customer loyalty.</li>"
        moats_found = True
    
    # Network Effects
    if any(phrase in content_lower for phrase in ["network effect", "platform advantage", "user base", "marketplace"]):
        moat_desc += "<li><strong>Network Effects:</strong> The company may benefit from network effects through its platform or user base.</li>"
        moats_found = True
    
    # IP
    if any(word in content_lower for word in ["patent", "intellectual property", "trademark", "proprietary", "copyright"]):
        moat_desc += "<li><strong>Intellectual Property:</strong> The company has patents or other intellectual property protections.</li>"
        moats_found = True
    
    # Scale
    if any(phrase in content_lower for phrase in ["economies of scale", "scale advantage", "market share", "largest", "leading"]):
        moat_desc += "<li><strong>Scale Advantage:</strong> The company benefits from economies of scale or market leadership.</li>"
        moats_found = True
    
    # Switching Costs
    if any(phrase in content_lower for phrase in ["switching cost", "lock-in", "retention", "recurring", "subscription"]):
        moat_desc += "<li><strong>Switching Costs:</strong> Customers face costs or difficulties in switching to competitors.</li>"
        moats_found = True
    
    # Regulatory
    if any(word in content_lower for word in ["regulation", "compliance", "license", "permit", "regulatory"]):
        moat_desc += "<li><strong>Regulatory Advantages:</strong> The company benefits from regulatory barriers to entry.</li>"
        moats_found = True
    
    if not moats_found:
        moat_desc += "<li>No clear competitive advantages were identified in the document.</li>"
    
    moat_desc += "</ul>"
    insights["moat"] += moat_desc
    
    # --- Financial Analysis ---
    financial_desc = "<p>Financial indicators extracted from the document:</p><ul>"
    
    # Look for revenue information
    revenue_found = False
    for financial_term in ["revenue", "sales", "turnover"]:
        if financial_term in content_lower:
            # Look for nearby numbers
            start_pos = content_lower.find(financial_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+100)]
            financial_desc += f"<li><strong>Revenue:</strong> Mentioned in the document. Full context: \"{context}\"</li>"
            revenue_found = True
            break
    
    if not revenue_found:
        financial_desc += "<li><strong>Revenue:</strong> No specific information found.</li>"
    
    # Look for profit information
    profit_found = False
    for profit_term in ["profit", "earnings", "net income", "ebitda", "margin"]:
        if profit_term in content_lower:
            start_pos = content_lower.find(profit_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+100)]
            financial_desc += f"<li><strong>Profitability:</strong> Mentioned in the document. Full context: \"{context}\"</li>"
            profit_found = True
            break
    
    if not profit_found:
        financial_desc += "<li><strong>Profitability:</strong> No specific information found.</li>"
    
    # Look for debt information
    debt_found = False
    for debt_term in ["debt", "leverage", "loan", "borrowing", "liability"]:
        if debt_term in content_lower:
            start_pos = content_lower.find(debt_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+100)]
            financial_desc += f"<li><strong>Debt:</strong> Mentioned in the document. Full context: \"{context}\"</li>"
            debt_found = True
            break
    
    if not debt_found:
        financial_desc += "<li><strong>Debt:</strong> No specific information found.</li>"
    
    financial_desc += "</ul>"
    insights["financial"] += financial_desc
    
    # --- Management Analysis ---
    management_desc = "<p>Management information extracted from the document:</p><ul>"
    
    # Look for management mentions
    management_found = False
    for mgmt_term in ["ceo", "chief executive", "president", "chairman", "director", "leadership", "management team"]:
        if mgmt_term in content_lower:
            start_pos = content_lower.find(mgmt_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+150)]
            management_desc += f"<li><strong>Leadership:</strong> Management mentioned in the document. Full context: \"{context}\"</li>"
            management_found = True
            break
    
    if not management_found:
        management_desc += "<li><strong>Leadership:</strong> No specific information found about management team.</li>"
    
    # Look for strategy mentions
    strategy_found = False
    for strategy_term in ["strategy", "vision", "mission", "goal", "plan", "objective"]:
        if strategy_term in content_lower:
            start_pos = content_lower.find(strategy_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+150)]
            management_desc += f"<li><strong>Strategy:</strong> Business strategy mentioned in the document. Full context: \"{context}\"</li>"
            strategy_found = True
            break
    
    if not strategy_found:
        management_desc += "<li><strong>Strategy:</strong> No specific information found about business strategy.</li>"
    
    management_desc += "</ul>"
    insights["management"] += management_desc
    
    return insights


# List of SEC CIK and ticker symbols for "Magnificent 7" companies
SEC_QUICK_ACCESS = [
    {"name": "Apple Inc.", "cik": "0000320193", "ticker": "AAPL"},
    {"name": "Microsoft Corporation", "cik": "0000789019", "ticker": "MSFT"},
    {"name": "Amazon.com, Inc.", "cik": "0001018724", "ticker": "AMZN"},
    {"name": "Alphabet Inc. (Google)", "cik": "0001652044", "ticker": "GOOGL"},
    {"name": "Meta Platforms, Inc. (Facebook)", "cik": "0001326801", "ticker": "META"},
    {"name": "Tesla, Inc.", "cik": "0001318605", "ticker": "TSLA"},
    {"name": "NVIDIA Corporation", "cik": "0000885639", "ticker": "NVDA"}
]

def get_latest_10k_url(cik):
    """
    Get the URL for the latest 10-K filing for a company by CIK
    """
    # Strip leading zeros from CIK
    cik = cik.lstrip('0')
    
    # Format the URL to the latest 10-K
    form_type = "10-K"
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/index.json"
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/", cik