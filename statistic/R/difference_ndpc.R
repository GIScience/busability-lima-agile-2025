library(sf)


hex_london <- st_read("/home/dabanto/Downloads/lima_final_plots/hex_lima_uuid.gpkg") 
pr_london1 <- st_read("/home/dabanto/Downloads/lima_final_plots/poi_ratio_lima/poi_ratio_lima_rush_hour.gpkg") %>% st_drop_geometry()
pr_london1 <- pr_london1 %>%
  filter(!(is.na(pois_count_bus) | pois_count_bus == 0 | is.na(pois_count_drive) | pois_count_drive == 0))
pr_london1$ndvi <- (pr_london1$pois_count_drive - pr_london1$pois_count_bus) / (pr_london1$pois_count_drive + pr_london1$pois_count_bus)

df_merge1 <- merge(x = hex_london, y = pr_london1[ , c("ndvi", "uuid")], by = "uuid", all.x=TRUE)


pr_london2 <- st_read("/home/dabanto/Downloads/lima_final_plots/poi_ratio_lima/poi_ratio_lima_priority_lane.gpkg") %>% st_drop_geometry()
pr_london2 <- pr_london2 %>%
  filter(!(is.na(pois_count_bus) | pois_count_bus == 0 | is.na(pois_count_drive) | pois_count_drive == 0))
pr_london2$ndvi_prio <- (pr_london2$pois_count_drive - pr_london2$pois_count_bus) / (pr_london2$pois_count_drive + pr_london2$pois_count_bus)

df_merge2 <- merge(x = hex_london, y = pr_london2[ , c("ndvi_prio", "uuid")], by = "uuid", all.x=TRUE)

df_merge2 <- df_merge2 %>% st_drop_geometry()

df_tot <- merge(df_merge1, df_merge2[c("uuid", "ndvi_prio")], by = "uuid", all.x = T)


df_filtered <- df_tot[!(is.na(df_tot$ndvi) & is.na(df_tot$ndvi_prio)), ]

df_filtered$diff <- (df_filtered$ndvi_prio - df_filtered$ndvi)

df_filtered <- df_filtered %>%
  filter(diff != 0)

df_filtered <- df_filtered %>%
  filter(diff <= 0) %>%             # Remove rows where col1 has positive values
  mutate(diff = abs(diff))    

df_filtered <- df_filtered %>% st_transform(32718)

#27700

mapview::mapview(df_filtered)


poSurf <- st_point_on_surface(df_filtered)


polynb <- poly2nb(df_filtered)

k1nb <- st_coordinates(poSurf) %>% 
  knearneigh(k = 1) %>% 
  knn2nb()

unionedNb <- union.nb(k1nb, polynb)

is.symmetric.nb(unionedNb)



## it's not symmetric

union_k1nbSym <- make.sym.nb(unionedNb)

## now it is symmetric

is.symmetric.nb(union_k1nbSym)


dlist2 <- nbdists(union_k1nbSym, st_coordinates(poSurf))
dlist2 <- lapply(dlist2, function(x) 1/x)
unionedListw_d2 <- nb2listw(union_k1nbSym, glist=dlist2, style = "W")


data.frame(weights=unlist(unionedListw_d2$weights)) %>%
  ggplot(mapping= aes(x= weights)) + 
  geom_histogram() +
  labs(title="Weight matrix" , subtitle = "unioned contiguity and knb=1 nb, idw p=1, W")




getLocalMoranFactor <- function(x, listw, pval, quadr = "mean", p.adjust.method ="holm", method="normal", nsim=999)
{
  if(! (quadr %in% c("mean", "median", "pysal")))
    stop("getLocalMoranFactor: quadr needs to be one of the following values: 'mean', 'median', 'pysal'")
  if(! (method %in% c("normal", "perm")))
    stop("getLocalMoranFactor: method needs to be one of the following values: 'normal', 'perm'")
  if(! (p.adjust.method %in% p.adjust.methods))
    stop(paste("getLocalMoranFactor: p.adjust.method needs to be one of the following values:", p.adjust.methods))
  
  # adjust for multiple testing
  if(method == "normal")
    lMc <- spdep::localmoran(x, listw= listw) 
  else
    lMc <- spdep::localmoran_perm(x, listw= listw, nsim=nsim)
  # using only the number of neighbors for correction, not the total number of spatial units
  lMc[,5] <-  p.adjustSP(lMc[,5], method = p.adjust.method, nb = listw$neighbours)
  lMcQuadr <- attr(lMc, "quadr")
  
  lMcFac <- as.character(lMcQuadr[, quadr])
  # which values are significant
  idx <- which(lMc[,5]> pval)
  lMcFac[idx] <- "Not sign."
  lMcFac <- factor(lMcFac, levels = c("Not sign.", "Low-Low", "Low-High", "High-Low",  "High-High"))
  return(lMcFac)
}



df_filtered$localM <- getLocalMoranFactor(df_filtered$diff, listw = unionedListw_d2, pval=0.05, method = "perm", nsim = 999)


localMcPalette <- c("white", "midnightblue", "lightblue", "lightpink", "red")

st_crs(df_filtered)

m1 <- tm_shape(df_filtered) + 
  tm_polygons(col="localM", palette=localMcPalette, lwd = 0.3,  
              legend.hist = FALSE, legend.reverse = TRUE, title = "Local Moran's I") +
  tm_layout(legend.outside = FALSE, 
            bg.color = NA,
            legend.position = c("left", "bottom"),
            legend.text.size = 1.2,  # Increase legend text size
            legend.title.size = 1.6, # Increase legend title size
            attr.outside = FALSE,
            outer.margins = c(0, 0, 0, 0),  # Remove outer margins
            title = 'Difference', 
            title.size = 1.4,             # Increase title size
            title.position = c('right', 'top')) + 
  tm_scale_bar(position = c("left", "bottom"), text.size = 0.5, lwd = 1.5)

m1

tmap_save(
  tm = m1, 
  filename = "/home/dabanto/Downloads/lima_final_plots/lima_cluster_diff2.png", 
  dpi = 300        
)










