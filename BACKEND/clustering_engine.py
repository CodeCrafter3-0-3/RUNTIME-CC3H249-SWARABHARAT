from collections import defaultdict
import math

class ClusteringEngine:
    def cluster_by_similarity(self, reports, threshold=0.7):
        clusters = []
        processed = set()
        
        for i, report1 in enumerate(reports):
            if i in processed:
                continue
            
            cluster = [report1]
            processed.add(i)
            
            for j, report2 in enumerate(reports[i+1:], start=i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_similarity(report1, report2)
                if similarity >= threshold:
                    cluster.append(report2)
                    processed.add(j)
            
            if len(cluster) >= 2:
                clusters.append({
                    'size': len(cluster),
                    'common_issue': report1.get('issue'),
                    'common_location': report1.get('location'),
                    'reports': cluster
                })
        
        return sorted(clusters, key=lambda x: x['size'], reverse=True)
    
    def _calculate_similarity(self, r1, r2):
        score = 0
        
        if r1.get('issue') == r2.get('issue'):
            score += 0.4
        if r1.get('location') == r2.get('location'):
            score += 0.3
        if r1.get('urgency') == r2.get('urgency'):
            score += 0.2
        if r1.get('emotion') == r2.get('emotion'):
            score += 0.1
        
        return score
    
    def find_outliers(self, reports):
        outliers = []
        
        # Find reports with unique combinations
        issue_location = defaultdict(int)
        for r in reports:
            key = f"{r.get('issue')}_{r.get('location')}"
            issue_location[key] += 1
        
        for r in reports:
            key = f"{r.get('issue')}_{r.get('location')}"
            if issue_location[key] == 1:
                outliers.append({
                    'report': r,
                    'reason': 'unique_combination',
                    'confidence': 0.8
                })
        
        return outliers[:10]
    
    def geographic_clustering(self, reports):
        location_groups = defaultdict(list)
        
        for r in reports:
            loc = r.get('location', 'Unknown')
            if loc and loc != 'Unknown':
                location_groups[loc].append(r)
        
        clusters = []
        for loc, group in location_groups.items():
            if len(group) >= 3:
                issue_dist = defaultdict(int)
                for r in group:
                    issue_dist[r.get('issue')] += 1
                
                clusters.append({
                    'location': loc,
                    'count': len(group),
                    'dominant_issue': max(issue_dist, key=issue_dist.get),
                    'issue_distribution': dict(issue_dist)
                })
        
        return sorted(clusters, key=lambda x: x['count'], reverse=True)

clustering_engine = ClusteringEngine()
