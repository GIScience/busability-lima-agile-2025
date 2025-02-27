library(tidyverse)  # Modern data science workflow
library(sf)
library(sp)
library(spdep)
library(rgdal)
library(tmap)
library(tmaptools)
library(grid)
library(gridExtra)
library(mapview)


hex_london <- st_read("/home/dabanto/Downloads/lima_final_plots/hex_lima_uuid.gpkg") 
pr_london1 <- st_read("/home/dabanto/Downloads/lima_final_plots/poi_ratio_lima/poi_ratio_lima_normal.gpkg") %>% st_drop_geometry()

pr_london <- pr_london1 %>%
  filter(!(is.na(pois_count_bus) | pois_count_bus == 0 | is.na(pois_count_drive) | pois_count_drive == 0))

pr_london$ndvi <- (pr_london$pois_count_drive - pr_london$pois_count_bus) / (pr_london$pois_count_drive + pr_london$pois_count_bus)


df_merge <- merge(x = hex_london, y = pr_london[ , c("ndvi", "uuid")], by = "uuid", all.x=TRUE)

df_merge <- df_merge %>%
  #filter(!uuid %in% c("0446fe3b-34be-4e4b-9959-3e5829d9056d", "fa0ed4c9-4651-465f-a048-793621954cf9")) %>% 
  filter(!is.na(ndvi))



tm_shape(df_merge) + 
  tm_fill("ndvi",
          palette = "Reds", 
          style = "quantile", 
          title = "%") +
  tm_borders(alpha=.4)  


df_merge <- df_merge %>% st_transform(32718)





poSurf <- st_point_on_surface(df_merge)


polynb <- poly2nb(df_merge)

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



df_merge$localM <- getLocalMoranFactor(df_merge$ndvi, listw = unionedListw_d2, pval=0.05, method = "perm", nsim = 999)



localMcPalette <- c("white", "midnightblue", "lightblue", "lightpink", "red")

m1 <- tm_shape(df_merge) + 
  tm_polygons(col="localM", palette=localMcPalette, lwd = 0.3,  
              legend.hist = FALSE, legend.reverse = TRUE, title = "Local Moran's I") +
  tm_layout(legend.outside = FALSE, 
            bg.color = NA,
            legend.position = c("left", "bottom"),
            legend.text.size = 0.8,  # Increase legend text size
            legend.title.size = 1.0, # Increase legend title size
            attr.outside = FALSE,
            outer.margins = c(0, 0, 0, 0),  # Remove outer margins
            title = 'Normal', 
            title.size = 1.2,             # Increase title size
            title.position = c('right', 'top')) + 
  tm_scale_bar(position = c("left", "bottom"), text.size = 0.5, lwd = 1.5)
m1

m2 <- tm_shape(df_merge) + 
  tm_polygons(col="localM", palette=localMcPalette, lwd = 0.3,  
              legend.hist = FALSE, legend.reverse = TRUE, title = "Local Moran's I") +
  tm_layout(legend.outside = FALSE, bg.color = NA,
            legend.position = c("left", "bottom"),
            legend.text.size = 0.8,  # Increase legend text size
            legend.title.size = 1.0, # Increase legend title size
            attr.outside = FALSE,
            outer.margins = c(0, 0, 0, 0),  # Remove outer margins
            title = 'Rush Hour', 
            title.size = 1.2, 
            title.position = c('right', 'top')) + 
  tm_scale_bar(position = c("left", "bottom"), text.size = 0.5, lwd = 1.5)
m2


m3 <- tm_shape(df_merge) + 
  tm_polygons(col="localM", palette=localMcPalette, lwd = 0.3,  
              legend.hist = FALSE, legend.reverse = TRUE, title = "Local Moran's I") +
  tm_layout(legend.outside = FALSE, bg.color = NA,
            legend.position = c("left", "bottom"),
            legend.text.size = 0.8,  # Increase legend text size
            legend.title.size = 1.0, # Increase legend title size
            attr.outside = FALSE,
            outer.margins = c(0, 0, 0, 0),  # Remove outer margins
            title = 'Rush Hour with Priority Lane', 
            title.size = 1.2, 
            title.position = c('right', 'top')) + 
  tm_scale_bar(position = c("left", "bottom"), text.size = 0.5, lwd = 1.5)

m3

t <- tmap_arrange(m1, m2, m3)

tmap_save(
  tm = t, 
  filename = "/home/dabanto/Downloads/lima_final_plots/lima_cluster.png", 
  width = 18,         # Width in inches
  height = 9,         # Height in inches (adjust for desired aspect ratio)
  dpi = 300           # High resolution (dots per inch)
)
















